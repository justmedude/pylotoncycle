import unittest

from pylotoncycle import PylotonCycle


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


if __name__ == "__main__":
    unittest.main()
