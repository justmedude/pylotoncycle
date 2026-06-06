# endpoint info derived from
# https://github.com/philosowaffle/postman_collections/blob/master/PelotonCycle/

# https://app.swaggerhub.com/apis/DovOps/peloton-unofficial-api/0.2.3

from .AutoRefreshingSession import AutoRefreshingSession
from .exceptions import PelotonAuthError
from .parser import ParseCyclingMetrics, ParseOutdoorRunMetrics


class PelotonLoginException(PelotonAuthError):
    pass


class PylotonCycle:
    def __init__(
        self,
        username=None,
        password=None,
        access_token=None,
        refresh_token=None,
        client_id="mgsmWCD0A8Qn6uz6mmqI6qeBNHH9IPwS",
        redirect_uri="https://members.onepeloton.com/callback",
        token_url="https://auth.onepeloton.com/oauth/token",
    ):
        self.base_url = "https://api.onepeloton.com"
        self.userid = None
        self.instructor_id_dict = {}
        if access_token and len(access_token) < 10:
            access_token = None
        if refresh_token and len(refresh_token) < 10:
            refresh_token = None
        if username and len(username) < 2:
            username = None
            password = None

        # The session is not initialized until we login and get tokens
        self.s = AutoRefreshingSession(
            username=username,
            password=password,
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            redirect_uri=redirect_uri,
            token_url=token_url,
        )
        self.GetMe()
        # print(f"Got me, id:{self.userid}")

    def GetAuthInfo(self):
        return self.s.get_auth_info()

    def GetMe(self):
        url = f"{self.base_url}/api/me"
        resp = self.s.get(url, timeout=10)

        if resp.status_code != 200:
            raise PelotonLoginException(
                f"Failed to get user info: HTTP {resp.status_code}"
            )

        try:
            data = resp.json()
        except ValueError as e:
            raise PelotonLoginException(f"Invalid API response: {e}")

        try:
            self.username = data["username"]
            self.userid = data["id"]
            self.total_workouts = data["total_workouts"]
        except KeyError as e:
            raise PelotonLoginException(f"Missing expected field: {e}")

        return data

    def GetSettings(self):
        url = "%s/api/user/%s/settings" % (self.base_url, self.userid)
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetUserOverviewById(self, userid=None, version=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/overview" % (self.base_url, userid)
        if version is not None:
            url = "%s?version=%s" % (url, version)

        resp = self.s.get(
            url,
            timeout=10,
            headers={"Peloton-Platform": "web"},
        ).json()
        return resp

    def GetCurrentChallenges(self, has_joined, userid=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/challenges/current?has_joined=%s" % (
            self.base_url,
            userid,
            str(has_joined).lower(),
        )
        resp = self.GetUrl(url)
        return resp

    def GetUpcomingChallenges(self, has_joined, userid=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/challenges/upcoming?has_joined=%s" % (
            self.base_url,
            userid,
            str(has_joined).lower(),
        )
        resp = self.GetUrl(url)
        return resp

    def GetChallengeById(self, challenge_id, userid=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/challenges/%s" % (
            self.base_url,
            userid,
            challenge_id,
        )
        resp = self.GetUrl(url)
        return resp

    def GetChallengeFriendsById(self, challenge_id, userid=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/challenges/%s/friends" % (
            self.base_url,
            userid,
            challenge_id,
        )
        resp = self.GetUrl(url)
        return resp

    def GetFollowingById(self, userid=None, page=0, limit=20, joins=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/following?page=%s&limit=%s" % (
            self.base_url,
            userid,
            page,
            limit,
        )
        if joins is not None:
            url = "%s&joins=%s" % (url, joins)

        resp = self.GetUrl(url)
        return resp

    def GetActivityCalendarById(self, userid=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/calendar" % (self.base_url, userid)
        resp = self.GetUrl(url)
        return resp

    def GetAchievementsById(self, userid=None):
        if userid is None:
            userid = self.userid

        url = "%s/api/user/%s/achievements" % (self.base_url, userid)
        resp = self.s.get(
            url,
            timeout=10,
            headers={"Peloton-Platform": "web"},
        ).json()
        return resp

    def GetBrowseCategories(self, library_type="on_demand"):
        url = "%s/api/browse_categories?library_type=%s" % (
            self.base_url,
            library_type,
        )
        resp = self.GetUrl(url)
        return resp

    def GetInstructors(self, page=0, limit=100):
        url = "%s/api/instructor?page=%s&limit=%s" % (
            self.base_url,
            page,
            limit,
        )
        resp = self.GetUrl(url)
        return resp

    def GetRideMetadataMappings(self):
        url = "%s/api/ride/metadata_mappings" % (self.base_url)
        resp = self.GetUrl(url)
        return resp

    def GetRideFilters(
        self,
        library_type=None,
        browse_category=None,
        include_icon_images=None,
    ):
        url = "%s/api/ride/filters" % (self.base_url)
        query_params = []

        if library_type is not None:
            query_params.append("library_type=%s" % library_type)

        if browse_category is not None:
            query_params.append("browse_category=%s" % browse_category)

        if include_icon_images is not None:
            query_params.append(
                "include_icon_images=%s" % str(include_icon_images).lower()
            )

        if query_params:
            url = "%s?%s" % (url, "&".join(query_params))

        resp = self.GetUrl(url)
        return resp

    def GetUrl(self, url):
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetWorkoutList(self, num_workouts=None):
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
            resp_instructor = {"name": None}

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

    def GetRideDetailsById(self, ride_id):
        url = "%s/api/ride/%s/details" % (self.base_url, ride_id)
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
        if not isinstance(metrics_data, dict):
            raise ValueError("metrics_data must be a dict")

        if metrics_data.get("location_data"):
            return ParseOutdoorRunMetrics(metrics_data)

        if (
            "metrics" in metrics_data
            and "seconds_since_pedaling_start" in metrics_data
        ):
            return ParseCyclingMetrics(metrics_data)

        raise ValueError("Unsupported metrics data shape")


if __name__ == "__main__":
    username = "My_Peloton_User_or_Email"
    password = "My_Peloton_Password"
    conn = PylotonCycle(username, password)
