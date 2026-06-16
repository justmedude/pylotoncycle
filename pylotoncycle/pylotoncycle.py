# endpoint info derived from
# https://github.com/philosowaffle/postman_collections/blob/master/PelotonCycle/

# https://app.swaggerhub.com/apis/DovOps/peloton-unofficial-api/0.2.3

from typing import Any, Dict, List, Optional

from .AutoRefreshingSession import AutoRefreshingSession
from .exceptions import PelotonAuthError
from .parser import ParseCyclingMetrics, ParseOutdoorRunMetrics


class PelotonLoginException(PelotonAuthError):
    """Raised when login to Peloton fails."""


class PylotonCycle:
    """Main class for interacting with the Peloton API."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client_id: str = "mgsmWCD0A8Qn6uz6mmqI6qeBNHH9IPwS",
        redirect_uri: str = "https://members.onepeloton.com/callback",
        token_url: str = "https://auth.onepeloton.com/oauth/token",
    ) -> None:
        """Initializes the PylotonCycle client.

        Args:
            username: Peloton username or email.
            password: Peloton password.
            access_token: Existing OAuth access token.
            refresh_token: Existing OAuth refresh token.
            client_id: OAuth client ID.
            redirect_uri: OAuth redirect URI.
            token_url: OAuth token endpoint URL.
        """
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

    def GetAuthInfo(self) -> Dict[str, Any]:
        """Returns the current authentication information.

        Returns:
            A dictionary containing authentication tokens and credentials.
        """
        return self.s.get_auth_info()

    def GetMe(self) -> Dict[str, Any]:
        """Fetches the current user's profile information.

        Returns:
            A dictionary containing user profile data.

        Raises:
            PelotonLoginException: If the request fails or returns invalid data.
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

    def GetSettings(self) -> Dict[str, Any]:
        """Fetches the current user's settings.

        Returns:
            A dictionary containing user settings.
        """
        url = f"{self.base_url}/api/user/{self.userid}/settings"
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetUserOverviewById(
        self,
        userid: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches an overview for a specific user.

        Args:
            userid: The user ID to fetch the overview for. Defaults to current user.
            version: Optional version parameter for the API.

        Returns:
            A dictionary containing the user overview.
        """
        if userid is None:
            userid = self.userid

        url = f"{self.base_url}/api/user/{userid}/overview"
        if version is not None:
            url = f"{url}?version={version}"

        resp = self.s.get(
            url,
            timeout=10,
            headers={"Peloton-Platform": "web"},
        ).json()
        return resp

    def GetCurrentChallenges(
        self, has_joined: bool, userid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches current challenges for a specific user.

        Args:
            has_joined: Filter by challenges the user has joined.
            userid: The user ID to fetch challenges for. Defaults to current user.

        Returns:
            A dictionary containing current challenges.
        """
        if userid is None:
            userid = self.userid

        url = (
            f"{self.base_url}/api/user/{userid}/challenges/current?"
            f"has_joined={str(has_joined).lower()}"
        )
        resp = self.GetUrl(url)
        return resp

    def GetUpcomingChallenges(
        self, has_joined: bool, userid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches upcoming challenges for a specific user.

        Args:
            has_joined: Filter by challenges the user has joined.
            userid: The user ID to fetch challenges for. Defaults to current user.

        Returns:
            A dictionary containing upcoming challenges.
        """
        if userid is None:
            userid = self.userid

        url = (
            f"{self.base_url}/api/user/{userid}/challenges/upcoming?"
            f"has_joined={str(has_joined).lower()}"
        )
        resp = self.GetUrl(url)
        return resp

    def GetChallengeById(
        self, challenge_id: str, userid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches details for a specific challenge.

        Args:
            challenge_id: The ID of the challenge.
            userid: The user ID. Defaults to current user.

        Returns:
            A dictionary containing challenge details.
        """
        if userid is None:
            userid = self.userid

        url = f"{self.base_url}/api/user/{userid}/challenges/{challenge_id}"
        resp = self.GetUrl(url)
        return resp

    def GetChallengeFriendsById(
        self, challenge_id: str, userid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches friends participating in a specific challenge.

        Args:
            challenge_id: The ID of the challenge.
            userid: The user ID. Defaults to current user.

        Returns:
            A dictionary containing challenge friends.
        """
        if userid is None:
            userid = self.userid

        url = (
            f"{self.base_url}/api/user/{userid}/challenges/"
            f"{challenge_id}/friends"
        )
        resp = self.GetUrl(url)
        return resp

    def GetFollowingById(
        self,
        userid: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
        joins: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches the list of users followed by a specific user.

        Args:
            userid: The user ID. Defaults to current user.
            page: Page number for pagination.
            limit: Number of results per page.
            joins: Optional joins parameter for the API.

        Returns:
            A dictionary containing the following list.
        """
        if userid is None:
            userid = self.userid

        url = (
            f"{self.base_url}/api/user/{userid}/following?"
            f"page={page}&limit={limit}"
        )
        if joins is not None:
            url = f"{url}&joins={joins}"

        resp = self.GetUrl(url)
        return resp

    def GetActivityCalendarById(
        self, userid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches the activity calendar for a specific user.

        Args:
            userid: The user ID. Defaults to current user.

        Returns:
            A dictionary containing the activity calendar.
        """
        if userid is None:
            userid = self.userid

        url = f"{self.base_url}/api/user/{userid}/calendar"
        resp = self.GetUrl(url)
        return resp

    def GetAchievementsById(
        self, userid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches achievements for a specific user.

        Args:
            userid: The user ID. Defaults to current user.

        Returns:
            A dictionary containing user achievements.
        """
        if userid is None:
            userid = self.userid

        url = f"{self.base_url}/api/user/{userid}/achievements"
        resp = self.s.get(
            url,
            timeout=10,
            headers={"Peloton-Platform": "web"},
        ).json()
        return resp

    def GetBrowseCategories(
        self, library_type: str = "on_demand"
    ) -> Dict[str, Any]:
        """Fetches browse categories for the library.

        Args:
            library_type: The type of library (e.g., 'on_demand').

        Returns:
            A dictionary containing browse categories.
        """
        url = (
            f"{self.base_url}/api/browse_categories?"
            f"library_type={library_type}"
        )
        resp = self.GetUrl(url)
        return resp

    def GetInstructors(
        self, page: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        """Fetches the list of instructors.

        Args:
            page: Page number for pagination.
            limit: Number of results per page.

        Returns:
            A dictionary containing the list of instructors.
        """
        url = f"{self.base_url}/api/instructor?page={page}&limit={limit}"
        resp = self.GetUrl(url)
        return resp

    def GetRideMetadataMappings(self) -> Dict[str, Any]:
        """Fetches metadata mappings for rides.

        Returns:
            A dictionary containing ride metadata mappings.
        """
        url = f"{self.base_url}/api/ride/metadata_mappings"
        resp = self.GetUrl(url)
        return resp

    def GetRideFilters(
        self,
        library_type: Optional[str] = None,
        browse_category: Optional[str] = None,
        include_icon_images: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Fetches available filters for rides.

        Args:
            library_type: Optional library type.
            browse_category: Optional browse category.
            include_icon_images: Whether to include icon images.

        Returns:
            A dictionary containing ride filters.
        """
        url = f"{self.base_url}/api/ride/filters"
        query_params = []

        if library_type is not None:
            query_params.append(f"library_type={library_type}")

        if browse_category is not None:
            query_params.append(f"browse_category={browse_category}")

        if include_icon_images is not None:
            query_params.append(
                f"include_icon_images={str(include_icon_images).lower()}"
            )

        if query_params:
            url = f"{url}?{'&'.join(query_params)}"

        resp = self.GetUrl(url)
        return resp

    def SearchUsers(self, user_query: str, limit: int = 40) -> Dict[str, Any]:
        """Searches for users by query string.

        Args:
            user_query: The search query (e.g., username).
            limit: Maximum number of results to return.

        Returns:
            A dictionary containing search results.
        """
        url = (
            f"{self.base_url}/api/user/search?"
            f"user_query={user_query}&limit={limit}"
        )
        resp = self.GetUrl(url)
        return resp

    def GetUserByIdOrUsername(
        self,
        user_name_or_id: str,
        is_onboarded: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Fetches user profile by ID or username.

        Args:
            user_name_or_id: The ID or username of the user.
            is_onboarded: Optional onboarded status filter.

        Returns:
            A dictionary containing user profile data.
        """
        url = f"{self.base_url}/api/user/{user_name_or_id}"

        if is_onboarded is not None:
            url = f"{url}?is_onboarded={str(is_onboarded).lower()}"

        resp = self.GetUrl(url)
        return resp

    def GetSubscriptions(self) -> Dict[str, Any]:
        """Fetches the current user's subscriptions.

        Returns:
            A dictionary containing subscription data.
        """
        url = f"{self.base_url}/api/v2/user/subscriptions"
        resp = self.GetUrl(url)
        return resp

    def GetReferralHistoryById(
        self, userid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches referral history for a specific user.

        Args:
            userid: The user ID. Defaults to current user.

        Returns:
            A dictionary containing referral history.
        """
        if userid is None:
            userid = self.userid

        url = f"{self.base_url}/api/user/{userid}/referral_history"
        resp = self.GetUrl(url)
        return resp

    def GetUrl(self, url: str) -> Dict[str, Any]:
        """Helper method to fetch JSON from a given URL.

        Args:
            url: The URL to fetch.

        Returns:
            The parsed JSON response.
        """
        resp = self.s.get(url, timeout=10).json()
        return resp

    def GetWorkoutList(
        self, num_workouts: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetches a list of workouts for the current user.

        Args:
            num_workouts: Number of workouts to fetch. Defaults to all.

        Returns:
            A list of dictionaries containing workout data.
        """
        if num_workouts is None:
            self.GetMe()
            num_workouts = self.total_workouts

        limit = 100
        pages = num_workouts // limit
        rem = num_workouts % limit

        base_workout_url = (
            f"{self.base_url}/api/user/{self.userid}/workouts?"
            "sort_by=-created"
        )

        workout_list = []
        current_page = 0

        while current_page < pages:
            url = f"{base_workout_url}&page={current_page}&limit={limit}"
            resp = self.s.get(url, timeout=10).json()
            workout_list.extend(resp["data"])
            current_page += 1

        if rem != 0:
            url = f"{base_workout_url}&page={current_page}&limit={limit}"
            resp = self.s.get(url, timeout=10).json()
            workout_list.extend(resp["data"][0:rem])

        return workout_list

    def GetRecentWorkouts(
        self, num_workouts: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetches detailed information for recent workouts.

        Args:
            num_workouts: Number of workouts to fetch. Defaults to all.

        Returns:
            A list of dictionaries containing detailed workout information.
        """
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

    def GetWorkoutSummaryById(self, workout_id: str) -> Dict[str, Any]:
        """Fetches summary for a specific workout.

        Args:
            workout_id: The ID of the workout.

        Returns:
            A dictionary containing the workout summary.
        """
        url = f"{self.base_url}/api/workout/{workout_id}"
        resp = self.GetUrl(url)
        return resp

    def GetWorkoutMetricsById(
        self, workout_id: str, frequency: int = 50
    ) -> Dict[str, Any]:
        """Fetches metrics for a specific workout.

        Args:
            workout_id: The ID of the workout.
            frequency: Sample frequency for performance data.

        Returns:
            A dictionary containing workout metrics.
        """
        performance_frequency = (
            f"?every_n={frequency}" if frequency > 0 else ""
        )
        url = (
            f"{self.base_url}/api/workout/{workout_id}/"
            f"performance_graph{performance_frequency}"
        )
        resp = self.GetUrl(url)
        return resp

    def GetWorkoutById(self, workout_id: str) -> Dict[str, Any]:
        """Fetches detailed information for a specific workout.

        Args:
            workout_id: The ID of the workout.

        Returns:
            A dictionary containing workout details.
        """
        url = f"{self.base_url}/api/workout/{workout_id}"
        resp = self.GetUrl(url)
        return resp

    def GetRideDetailsById(
        self, ride_id: str, stream_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches details for a specific ride.

        Args:
            ride_id: The ID of the ride.
            stream_source: Optional stream source parameter.

        Returns:
            A dictionary containing ride details.
        """
        url = f"{self.base_url}/api/ride/{ride_id}/details"
        if stream_source is not None:
            url = f"{url}?stream_source={stream_source}"
        resp = self.GetUrl(url)
        return resp

    def GetArchivedRides(
        self,
        browse_category: Optional[str] = None,
        limit: int = 100,
        content_format: Optional[str] = None,
        page: int = 0,
        sort_by: Optional[str] = None,
        is_favorite_ride: Optional[bool] = None,
        desc: Optional[bool] = None,
        instructor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches archived rides with optional filters.

        Args:
            browse_category: Filter by browse category.
            limit: Number of results per page.
            content_format: Filter by content format.
            page: Page number for pagination.
            sort_by: Field to sort by.
            is_favorite_ride: Filter by favorite rides.
            desc: Whether to sort in descending order.
            instructor_id: Filter by instructor ID.

        Returns:
            A dictionary containing archived rides.
        """
        url = f"{self.base_url}/api/v2/ride/archived"
        query_params = []

        if browse_category is not None:
            query_params.append(f"browse_category={browse_category}")

        if limit is not None:
            query_params.append(f"limit={limit}")

        if content_format is not None:
            query_params.append(f"content_format={content_format}")

        if page is not None:
            query_params.append(f"page={page}")

        if sort_by is not None:
            query_params.append(f"sort_by={sort_by}")

        if is_favorite_ride is not None:
            query_params.append(
                f"is_favorite_ride={str(is_favorite_ride).lower()}"
            )

        if desc is not None:
            query_params.append(f"desc={str(desc).lower()}")

        if instructor_id is not None:
            query_params.append(f"instructor_id={instructor_id}")

        if query_params:
            url = f"{url}?{'&'.join(query_params)}"

        resp = self.GetUrl(url)
        return resp

    def GetLiveRides(
        self,
        exclude_complete: Optional[bool] = None,
        content_provider: Optional[str] = None,
        browse_category: Optional[str] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None,
        end: Optional[int] = None,
        exclude_live_in_studio_only: Optional[bool] = None,
        ignore_class_language_preferences: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Fetches live rides with optional filters.

        Args:
            exclude_complete: Whether to exclude completed rides.
            content_provider: Filter by content provider.
            browse_category: Filter by browse category.
            start: Start timestamp filter.
            limit: Number of results to return.
            end: End timestamp filter.
            exclude_live_in_studio_only: Whether to exclude studio-only rides.
            ignore_class_language_preferences: Whether to ignore language prefs.

        Returns:
            A dictionary containing live rides.
        """
        url = f"{self.base_url}/api/v3/ride/live"
        query_params = []

        if exclude_complete is not None:
            query_params.append(
                f"exclude_complete={str(exclude_complete).lower()}"
            )

        if content_provider is not None:
            query_params.append(f"content_provider={content_provider}")

        if browse_category is not None:
            query_params.append(f"browse_category={browse_category}")

        if start is not None:
            query_params.append(f"start={start}")

        if limit is not None:
            query_params.append(f"limit={limit}")

        if end is not None:
            query_params.append(f"end={end}")

        if exclude_live_in_studio_only is not None:
            query_params.append(
                "exclude_live_in_studio_only="
                f"{str(exclude_live_in_studio_only).lower()}"
            )

        if ignore_class_language_preferences is not None:
            query_params.append(
                "ignore_class_language_preferences="
                f"{str(ignore_class_language_preferences).lower()}"
            )

        if query_params:
            url = f"{url}?{'&'.join(query_params)}"

        resp = self.GetUrl(url)
        return resp

    def GetRecentFollowingWorkoutsByRideId(
        self,
        ride_id: str,
        joins: Optional[str] = None,
        limit: int = 20,
        page: int = 0,
        sort_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches recent workouts from followed users for a specific ride.

        Args:
            ride_id: The ID of the ride.
            joins: Optional joins parameter.
            limit: Number of results to return.
            page: Page number for pagination.
            sort_by: Field to sort by.

        Returns:
            A dictionary containing recent following workouts.
        """
        url = f"{self.base_url}/api/ride/{ride_id}/recent_following_workouts"
        query_params = []

        if joins is not None:
            query_params.append(f"joins={joins}")

        if limit is not None:
            query_params.append(f"limit={limit}")

        if page is not None:
            query_params.append(f"page={page}")

        if sort_by is not None:
            query_params.append(f"sort_by={sort_by}")

        if query_params:
            url = f"{url}?{'&'.join(query_params)}"

        resp = self.GetUrl(url)
        return resp

    def GetInstructorById(self, instructor_id: str) -> Dict[str, Any]:
        """Fetches detailed information for a specific instructor.

        Args:
            instructor_id: The ID of the instructor.

        Returns:
            A dictionary containing instructor details.
        """
        if instructor_id in self.instructor_id_dict:
            return self.instructor_id_dict[instructor_id]

        url = f"{self.base_url}/api/instructor/{instructor_id}"
        resp = self.GetUrl(url)
        self.instructor_id_dict[instructor_id] = resp
        return resp

    def GetFollowersById(self, userid: Optional[str] = None) -> Dict[str, Any]:
        """Fetches the list of followers for a specific user.

        Args:
            userid: The user ID. Defaults to current user.

        Returns:
            A dictionary containing the followers list.
        """
        if userid is None:
            userid = self.userid
        url = f"{self.base_url}/api/user/{userid}/followers"
        resp = self.GetUrl(url)
        return resp

    def ParseMetricsData(
        self, metrics_data: Dict[str, Any]
    ) -> Dict[int, Dict[str, Any]]:
        """Parses performance metrics data based on its shape.

        Supports both cycling and outdoor run metrics.

        Args:
            metrics_data: The raw metrics data dictionary.

        Returns:
            A dictionary keyed by offset seconds containing metrics.

        Raises:
            ValueError: If metrics_data is not a dict or has an unsupported shape.
        """
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
