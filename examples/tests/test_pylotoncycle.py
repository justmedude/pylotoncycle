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
