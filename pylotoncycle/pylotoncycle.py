"""
PylotonCycle - Python library for accessing Peloton workout data.

Endpoint info derived from:
- https://github.com/philosowaffle/postman_collections/blob/master/PelotonCycle/
- https://app.swaggerhub.com/apis/DovOps/peloton-unofficial-api/0.2.3
"""

from .AutoRefreshingSession import AutoRefreshingSession


class PelotonLoginException(Exception):
    """Exception raised when authentication or user info retrieval fails."""

    pass


class PylotonCycle:
    """
    Main client for interacting with the Peloton API.

    Provides methods to fetch user data, workouts, instructors, and more.
    Handles OAuth authentication automatically via AutoRefreshingSession.

    Args:
        username: Peloton account username or email.
        password: Peloton account password.
        access_token: OAuth access token (if already obtained).
        refresh_token: OAuth refresh token (if already obtained).
        client_id: OAuth client ID.
        redirect_uri: OAuth redirect URI.
        token_url: OAuth token endpoint URL.

    Raises:
        PelotonLoginException: If authentication fails or user info
            cannot be retrieved.

    Example:
        >>> conn = PylotonCycle(username="user@example.com",
        ...                     password="secret")
        >>> workouts = conn.GetRecentWorkouts(5)
    """

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

    def GetAuthInfo(self):
        """
        Get current authentication information.

        Returns:
            dict: Authentication data including access_token, refresh_token,
                username, password, client_id, and redirect_uri.
        """
        return self.s.get_auth_info()

    def GetMe(self):
        """
        Fetch and store the current user's profile information.

        Updates instance attributes: username, userid, total_workouts.

        Returns:
            dict: Full user profile data from the API.

        Raises:
            PelotonLoginException: If the request fails or response is invalid.
        """
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
        """
        Fetch the current user's settings.

        Returns:
            dict: User settings data from the API.
        """
        url = "%s/api/user/%s/settings" % (self.base_url, self.userid)
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetUrl(self, url):
        """
        Make a GET request to any URL and return JSON response.

        Args:
            url: The full URL to request.

        Returns:
            dict: Parsed JSON response.
        """
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetWorkoutList(self, num_workouts=None):
        """
        Fetch a list of workout summaries for the current user.

        Args:
            num_workouts: Number of workouts to fetch. If None, fetches all.

        Returns:
            list: List of workout summary dictionaries, sorted by most recent.
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
        """
        Fetch detailed workout data including performance metrics.

        For each workout, fetches the full workout details, performance
        graph data, and instructor information.

        Args:
            num_workouts: Number of workouts to fetch. If None, fetches all.

        Returns:
            list: List of workout dictionaries with performance_graph
                and instructor_name fields added.
        """
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
        """
        Fetch workout summary by ID.

        Note: This method is identical to GetWorkoutById and may be
        deprecated in a future version.

        Args:
            workout_id: The unique identifier for the workout.

        Returns:
            dict: Workout summary data.
        """
        url = "%s/api/workout/%s" % (self.base_url, workout_id)
        resp = self.GetUrl(url)
        return resp

    def GetWorkoutMetricsById(self, workout_id, frequency=50):
        """
        Fetch performance metrics for a workout.

        Args:
            workout_id: The unique identifier for the workout.
            frequency: Sample every N seconds. Use 0 for all data points.
                Defaults to 50.

        Returns:
            dict: Performance graph data including metrics like cadence,
                resistance, output, speed, and heart rate over time.
        """
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
        """
        Fetch full workout details by ID.

        Args:
            workout_id: The unique identifier for the workout.

        Returns:
            dict: Full workout data including ride info, stats, and metadata.
        """
        url = "%s/api/workout/%s" % (self.base_url, workout_id)
        resp = self.GetUrl(url)
        return resp

    def GetInstructorById(self, instructor_id):
        """
        Fetch instructor details by ID.

        Results are cached to avoid redundant API calls.

        Args:
            instructor_id: The unique identifier for the instructor.

        Returns:
            dict: Instructor profile data.
        """
        if instructor_id in self.instructor_id_dict:
            return self.instructor_id_dict[instructor_id]

        url = "%s/api/instructor/%s" % (self.base_url, instructor_id)
        resp = self.GetUrl(url)
        self.instructor_id_dict[instructor_id] = resp
        return resp

    def GetFollowersById(self, userid=None):
        """
        Fetch followers for a user.

        Args:
            userid: The user ID to fetch followers for.
                Defaults to current user.

        Returns:
            dict: Follower data including list of followers.
        """
        if userid is None:
            userid = self.userid
        url = "%s/api/user/%s/followers" % (self.base_url, userid)
        resp = self.GetUrl(url)
        return resp

    def ParseMetricsData(self, metrics_data):
        """
        Parse raw metrics data into a structured format.

        Note: Not yet implemented. Use ParseCyclingMetrics or
        ParseOutdoorRunMetrics from pylotoncycle.parser instead.

        Args:
            metrics_data: Raw metrics data from GetWorkoutMetricsById.

        Returns:
            None: Not implemented.
        """
        pass


if __name__ == "__main__":
    username = "My_Peloton_User_or_Email"
    password = "My_Peloton_Password"
    conn = PylotonCycle(username, password)
