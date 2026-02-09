# endpoint info derived from
# https://github.com/philosowaffle/postman_collections/blob/master/PelotonCycle/

# https://app.swaggerhub.com/apis/DovOps/peloton-unofficial-api/0.2.3

import base64
import hashlib
import json
import secrets
import urllib.parse

import requests
from bs4 import BeautifulSoup


class PelotonLoginException(Exception):
    pass


class PylotonCycle:
    def __init__(self, username, password):
        self.base_url = "https://api.onepeloton.com"
        self.s = requests.Session()
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "pylotoncycle",
        }

        # Initialize a couple of variables that will get reused
        # userid - our userid
        # instructor_id_dict - dictionary that will allow us to cache
        #                      information
        #                      format is: instructor_id : instructor_dict
        self.userid = None
        self.instructor_id_dict = {}

        self.login(username, password)

    # OAuth 2.0 PKCE constants (Auth0-based)
    AUTH_DOMAIN = "auth.onepeloton.com"
    CLIENT_ID = "WVoJxVDdPoFx4RNewvvg6ch2mZ7bwnsM"
    REDIRECT_URI = "https://members.onepeloton.com/callback"
    AUDIENCE = "https://api.onepeloton.com/"
    SCOPE = "offline_access openid peloton-api.members:default"
    AUTH0_CLIENT = base64.b64encode(
        json.dumps({"name": "auth0.js-ulp", "version": "9.14.3"}).encode()
    ).decode()

    def login(self, username, password):
        # Step 1: Generate PKCE parameters
        code_verifier = secrets.token_urlsafe(48)[:64]
        code_challenge = (
            base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            )
            .rstrip(b"=")
            .decode()
        )
        state = secrets.token_urlsafe(24)[:32]
        nonce = secrets.token_urlsafe(24)[:32]

        # Step 2: GET /authorize to start the OAuth flow and get CSRF token
        authorize_url = f"https://{self.AUTH_DOMAIN}/authorize"
        authorize_params = {
            "response_type": "code",
            "code_challenge_method": "S256",
            "code_challenge": code_challenge,
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "scope": self.SCOPE,
            "audience": self.AUDIENCE,
            "state": state,
            "nonce": nonce,
        }
        resp = self.s.get(authorize_url, params=authorize_params, timeout=30)
        resp.raise_for_status()

        # Extract Auth0's internal state from the final redirect URL
        parsed_url = urllib.parse.urlparse(resp.url)
        url_params = urllib.parse.parse_qs(parsed_url.query)
        auth0_state = url_params.get("state", [None])[0]
        if auth0_state:
            state = auth0_state

        csrf_token = self.s.cookies.get("_csrf")
        if not csrf_token:
            raise PelotonLoginException(
                "Failed to obtain CSRF token from Auth0"
            )

        # Step 3: POST credentials to /usernamepassword/login
        login_url = f"https://{self.AUTH_DOMAIN}/usernamepassword/login"
        login_payload = {
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "tenant": "peloton-prod",
            "response_type": "code",
            "scope": self.SCOPE,
            "audience": self.AUDIENCE,
            "state": state,
            "nonce": nonce,
            "connection": "pelo-user-password",
            "username": username,
            "password": password,
            "_csrf": csrf_token,
            "sso": "true",
            "_intstate": "deprecated",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        login_headers = {
            "Auth0-Client": self.AUTH0_CLIENT,
            "Content-Type": "application/json",
        }
        resp = self.s.post(
            login_url, json=login_payload, headers=login_headers, timeout=30
        )
        if resp.status_code != 200:
            raise PelotonLoginException(
                f"Login failed (HTTP {resp.status_code}): {resp.text}"
            )

        # Step 4: Parse the HTML response for hidden form fields
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form")
        if not form:
            raise PelotonLoginException(
                "Login failed: no callback form in response (bad credentials?)"
            )

        form_action = form.get("action")
        # Resolve relative URLs against the Auth0 domain
        if form_action and form_action.startswith("/"):
            form_action = f"https://{self.AUTH_DOMAIN}{form_action}"
        form_data = {}
        for inp in form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            value = inp.get("value", "")
            if name:
                form_data[name] = value

        # Step 5: POST the hidden form to get the authorization code
        # Disable auto-redirect so we can capture the code from the
        # Location header
        resp = self.s.post(
            form_action, data=form_data, allow_redirects=False, timeout=30
        )

        # Follow redirects manually to find the one with ?code=
        auth_code = None
        max_redirects = 10
        while resp.is_redirect and max_redirects > 0:
            location = resp.headers.get("Location", "")
            # Resolve relative redirect URLs
            if location.startswith("/"):
                location = f"https://{self.AUTH_DOMAIN}{location}"
            parsed = urllib.parse.urlparse(location)
            query_params = urllib.parse.parse_qs(parsed.query)
            if "code" in query_params:
                auth_code = query_params["code"][0]
                break
            resp = self.s.get(location, allow_redirects=False, timeout=30)
            max_redirects -= 1

        if not auth_code:
            raise PelotonLoginException(
                "Failed to obtain authorization code from OAuth callback"
            )

        # Step 6: Exchange authorization code for access token
        token_url = f"https://{self.AUTH_DOMAIN}/oauth/token"
        token_payload = {
            "grant_type": "authorization_code",
            "client_id": self.CLIENT_ID,
            "code": auth_code,
            "code_verifier": code_verifier,
            "redirect_uri": self.REDIRECT_URI,
        }
        resp = self.s.post(token_url, json=token_payload, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise PelotonLoginException("No access_token in token response")

        # Step 7: Set Bearer token for all subsequent API calls
        self.s.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
            }
        )

        # Get user_id from /api/me (no longer returned by login response)
        me = self.GetMe()
        self.userid = me["id"]

    def GetMe(self):
        url = "%s/api/me" % self.base_url
        resp = self.s.get(url, timeout=10).json()
        self.username = resp["username"]
        self.userid = resp["id"]
        self.total_workouts = resp["total_workouts"]
        return resp

    def GetSettings(self):
        url = "%s/api/user/%s/settings" % (self.base_url, self.userid)
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetUrl(self, url):
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetWorkoutList(self, num_workouts=None):
        """
        Generally, not intended to call this directly, but
        rather through a helper function.
        num_workouts - specify the X most recent workouts to fetch. If left
                       as None, it will fetch all the workouts
        """
        if num_workouts is None:
            self.GetMe()
            num_workouts = self.total_workouts

        limit = 100
        pages = num_workouts // limit
        rem = num_workouts % limit

        base_workout_url = "%s/api/user/%s/workouts?sort_by=-created" % (
            self.base_url,
            self.userid,
        )

        workout_list = []
        current_page = 0

        while current_page < pages:
            url = "%s&page=%s&limit=%s" % (
                base_workout_url,
                current_page,
                limit,
            )
            resp = self.s.get(url, timeout=10).json()
            workout_list.extend(resp["data"])
            current_page += 1

        # if we have a remainder to fetch, then do another
        # call and extend on only that numbder of results
        if rem != 0:
            url = "%s&page=%s&limit=%s" % (
                base_workout_url,
                current_page,
                limit,
            )
            resp = self.s.get(url, timeout=10).json()
            workout_list.extend(resp["data"][0:rem])

        return workout_list

    def GetRecentWorkouts(self, num_workouts=None):
        workout_list = self.GetWorkoutList(num_workouts)
        workouts_info = []

        for i in workout_list:
            workout_id = i["id"]

            performance_graph = self.GetWorkoutMetricsById(workout_id)
            resp_workout = self.GetWorkoutById(workout_id)

            if "instructor_id" in resp_workout["ride"]:
                instructor_id = resp_workout["ride"]["instructor_id"]
                resp_instructor = self.GetInstructorById(instructor_id)
            elif "instructor" in resp_workout["ride"]:
                resp_instructor = {
                    "name": resp_workout["ride"]["instructor"]["name"]
                }

            resp_workout["performance_graph"] = performance_graph
            try:
                resp_workout["instructor_name"] = resp_instructor["name"]
            except KeyError:
                resp_workout["instructor_name"] = None
            workouts_info.append(resp_workout)
        return workouts_info

    def GetWorkoutSummaryById(self, workout_id):
        url = "%s/api/workout/%s" % (self.base_url, workout_id)
        resp = self.GetUrl(url)
        return resp

    def GetWorkoutMetricsById(self, workout_id, frequency=50):
        performance_frequency = (
            "?every_n=%s" % (frequency) if frequency > 0 else ""
        )
        url = "%s/api/workout/%s/performance_graph%s" % (
            self.base_url,
            workout_id,
            performance_frequency,
        )
        resp = self.GetUrl(url)
        return resp

    def GetWorkoutById(self, workout_id):
        url = "%s/api/workout/%s" % (self.base_url, workout_id)
        resp = self.GetUrl(url)
        return resp

    def GetInstructorById(self, instructor_id):
        if instructor_id in self.instructor_id_dict:
            return self.instructor_id_dict[instructor_id]

        url = "%s/api/instructor/%s" % (self.base_url, instructor_id)
        resp = self.GetUrl(url)
        self.instructor_id_dict[instructor_id] = resp
        return resp

    def GetFollowersById(self, userid=None):
        if userid is None:
            userid = self.userid
        url = "%s/api/user/%s/followers" % (self.base_url, userid)
        resp = self.GetUrl(url)
        return resp

    def ParseMetricsData(self, metrics_data):
        # TODO
        pass


if __name__ == "__main__":
    username = "My_Peloton_User_or_Email"
    password = "My_Peloton_Password"
    conn = PylotonCycle(username, password)
