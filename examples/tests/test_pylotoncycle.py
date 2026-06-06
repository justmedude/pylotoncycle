import unittest

from pylotoncycle import PylotonCycle


class FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, json_data):
        self.json_data = json_data
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.json_data)


class TestPylotonCycle(unittest.TestCase):
    def test_recent_workouts_handles_missing_instructor_fields(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.GetWorkoutMetricsById = lambda workout_id: {"x": 1}
        client.GetWorkoutById = lambda workout_id: {
            "ride": {"title": "Test Ride", "duration": 600},
            "instructor_name": None,
        }
        client.GetInstructorById = lambda instructor_id: {"name": "Ignored"}
        client.GetWorkoutList = lambda num_workouts=None: [{"id": "w1"}]

        result = PylotonCycle.GetRecentWorkouts(client, num_workouts=1)

        self.assertIsNone(result[0]["instructor_name"])
        self.assertEqual(result[0]["performance_graph"], {"x": 1})

    def test_get_user_overview_uses_current_user_and_platform_header(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.s = FakeSession({"workout_counts": {}})

        result = PylotonCycle.GetUserOverviewById(client)

        self.assertEqual(result, {"workout_counts": {}})
        self.assertEqual(
            client.s.calls,
            [
                (
                    "https://api.example.com/api/user/user-1/overview",
                    {
                        "timeout": 10,
                        "headers": {"Peloton-Platform": "web"},
                    },
                )
            ],
        )

    def test_get_user_overview_accepts_userid_and_version(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.s = FakeSession({"streaks": {}})

        result = PylotonCycle.GetUserOverviewById(
            client,
            userid="user-2",
            version=1,
        )

        self.assertEqual(result, {"streaks": {}})
        self.assertEqual(
            client.s.calls[0][0],
            "https://api.example.com/api/user/user-2/overview?version=1",
        )
        self.assertEqual(
            client.s.calls[0][1]["headers"],
            {"Peloton-Platform": "web"},
        )

    def test_get_ride_details_by_id_uses_ride_details_endpoint(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetRideDetailsById(client, "ride-1")

        self.assertEqual(
            result,
            {"url": "https://api.example.com/api/ride/ride-1/details"},
        )

    def test_get_ride_details_by_id_accepts_stream_source(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetRideDetailsById(
            client,
            "ride-1",
            stream_source="web",
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/ride/ride-1/details"
                    "?stream_source=web"
                )
            },
        )

    def test_get_archived_rides_uses_defaults(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetArchivedRides(client)

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/v2/ride/archived"
                    "?limit=100&page=0"
                )
            },
        )

    def test_get_archived_rides_supports_query_params(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetArchivedRides(
            client,
            browse_category="cycling",
            limit=25,
            content_format="audio",
            page=3,
            sort_by="trending",
            is_favorite_ride=True,
            desc=False,
            instructor_id="instructor-1",
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/v2/ride/archived"
                    "?browse_category=cycling&limit=25&content_format=audio"
                    "&page=3&sort_by=trending&is_favorite_ride=true"
                    "&desc=false&instructor_id=instructor-1"
                )
            },
        )

    def test_get_live_rides_supports_query_params(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetLiveRides(
            client,
            exclude_complete=True,
            content_provider="peloton",
            browse_category="cycling",
            start="2026-06-06T00:00:00Z",
            limit=10,
            end="2026-06-06T01:00:00Z",
            exclude_live_in_studio_only=False,
            ignore_class_language_preferences=True,
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/v3/ride/live"
                    "?exclude_complete=true&content_provider=peloton"
                    "&browse_category=cycling&start=2026-06-06T00:00:00Z"
                    "&limit=10&end=2026-06-06T01:00:00Z"
                    "&exclude_live_in_studio_only=false"
                    "&ignore_class_language_preferences=true"
                )
            },
        )

    def test_get_recent_following_workouts_by_ride_id_uses_defaults(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetRecentFollowingWorkoutsByRideId(
            client,
            "ride-1",
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/ride/ride-1/"
                    "recent_following_workouts?limit=20&page=0"
                )
            },
        )

    def test_get_recent_following_workouts_by_ride_id_supports_query_params(
        self,
    ):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetRecentFollowingWorkoutsByRideId(
            client,
            "ride-1",
            joins="ride,ride.instructor",
            limit=5,
            page=2,
            sort_by="-created_at",
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/ride/ride-1/"
                    "recent_following_workouts?joins=ride,ride.instructor"
                    "&limit=5&page=2&sort_by=-created_at"
                )
            },
        )

    def test_get_current_challenges_uses_default_userid(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetCurrentChallenges(client, has_joined=True)

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/user/user-1/"
                    "challenges/current?has_joined=true"
                )
            },
        )

    def test_get_upcoming_challenges_accepts_userid(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetUpcomingChallenges(
            client,
            has_joined=False,
            userid="user-2",
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/user/user-2/"
                    "challenges/upcoming?has_joined=false"
                )
            },
        )

    def test_get_challenge_by_id_uses_challenge_endpoint(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetChallengeById(client, "challenge-1")

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/user/user-1/"
                    "challenges/challenge-1"
                )
            },
        )

    def test_get_challenge_friends_by_id_uses_friends_endpoint(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetChallengeFriendsById(
            client,
            "challenge-1",
            userid="user-2",
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/user/user-2/"
                    "challenges/challenge-1/friends"
                )
            },
        )

    def test_get_following_by_id_uses_defaults(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetFollowingById(client)

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/user/user-1/"
                    "following?page=0&limit=20"
                )
            },
        )

    def test_get_following_by_id_accepts_options(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetFollowingById(
            client,
            userid="user-2",
            page=2,
            limit=5,
            joins="relationship",
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/user/user-2/"
                    "following?page=2&limit=5&joins=relationship"
                )
            },
        )

    def test_get_activity_calendar_by_id_uses_calendar_endpoint(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetActivityCalendarById(
            client,
            userid="user-2",
        )

        self.assertEqual(
            result,
            {"url": "https://api.example.com/api/user/user-2/calendar"},
        )

    def test_get_achievements_by_id_uses_platform_header(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.userid = "user-1"
        client.s = FakeSession({"categories": []})

        result = PylotonCycle.GetAchievementsById(client)

        self.assertEqual(result, {"categories": []})
        self.assertEqual(
            client.s.calls,
            [
                (
                    "https://api.example.com/api/user/user-1/achievements",
                    {
                        "timeout": 10,
                        "headers": {"Peloton-Platform": "web"},
                    },
                )
            ],
        )

    def test_get_browse_categories_uses_default_library_type(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetBrowseCategories(client)

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/browse_categories"
                    "?library_type=on_demand"
                )
            },
        )

    def test_get_instructors_uses_page_and_limit(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetInstructors(client, page=2, limit=25)

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/instructor?page=2&limit=25"
                )
            },
        )

    def test_get_ride_metadata_mappings_uses_expected_endpoint(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetRideMetadataMappings(client)

        self.assertEqual(
            result,
            {"url": ("https://api.example.com/api/ride/metadata_mappings")},
        )

    def test_get_ride_filters_supports_optional_query_params(self):
        client = PylotonCycle.__new__(PylotonCycle)
        client.base_url = "https://api.example.com"
        client.GetUrl = lambda url: {"url": url}

        result = PylotonCycle.GetRideFilters(
            client,
            library_type="on_demand",
            browse_category="cycling",
            include_icon_images=True,
        )

        self.assertEqual(
            result,
            {
                "url": (
                    "https://api.example.com/api/ride/filters"
                    "?library_type=on_demand&browse_category=cycling"
                    "&include_icon_images=true"
                )
            },
        )

    def test_parse_metrics_data_handles_cycling_payload(self):
        client = PylotonCycle.__new__(PylotonCycle)
        metrics_data = {
            "duration": 10,
            "location_data": [],
            "segment_list": [
                {
                    "name": "Warm Up",
                    "start_time_offset": 0,
                    "length": 10,
                }
            ],
            "seconds_since_pedaling_start": [0, 5],
            "metrics": [
                {
                    "slug": "cadence",
                    "values": [80, 90],
                },
                {
                    "slug": "output",
                    "values": [120, 150],
                },
            ],
        }

        result = PylotonCycle.ParseMetricsData(client, metrics_data)

        self.assertEqual(
            result,
            {
                0: {
                    "cadence": 80,
                    "output": 120,
                    "segment": "Warm Up",
                },
                5: {
                    "cadence": 90,
                    "output": 150,
                    "segment": "Warm Up",
                },
            },
        )

    def test_parse_metrics_data_handles_outdoor_run_payload(self):
        client = PylotonCycle.__new__(PylotonCycle)
        metrics_data = {
            "segment_list": [
                {
                    "id": "segment-1",
                    "name": "Run",
                    "metrics_type": "outdoor_run",
                }
            ],
            "location_data": [
                {
                    "segment_id": "segment-1",
                    "coordinates": [
                        {
                            "seconds_offset_from_start": 0,
                            "latitude": 42.1,
                            "longitude": -71.2,
                        }
                    ],
                }
            ],
        }

        result = PylotonCycle.ParseMetricsData(client, metrics_data)

        self.assertEqual(result[0]["latitude"], 42.1)
        self.assertEqual(result[0]["longitude"], -71.2)
        self.assertEqual(result[0]["segment_name"], "Run")
        self.assertEqual(result[0]["segment_metrics_type"], "outdoor_run")

    def test_parse_metrics_data_rejects_unknown_payload(self):
        client = PylotonCycle.__new__(PylotonCycle)

        with self.assertRaises(ValueError):
            PylotonCycle.ParseMetricsData(client, {"duration": 10})


if __name__ == "__main__":
    unittest.main()
