import unittest
from workouts_to_ics import generate_description


class TestGenerateDescription(unittest.TestCase):

    def test_just_ride_description(self):
        """
        Test case to verify the description generated for a 'Just Ride' workout.
        """
        workout = {
            "ride": {
                "title": "21 min Just Ride",
                "duration": 1273,
                "instructor": {
                    "name": "JUST RIDE",
                    "image_url": "https://s3.amazonaws.com/peloton-ride-images/just-ride-indoor.png"
                }
            },
            "instructor_name": "JUST RIDE",
            "leaderboard_rank": None,
            "total_leaderboard_users": None,
            "ftp_info": {
                "ftp": None,
                "ftp_source": None,
                "ftp_workout_id": None
            }
        }
        expected_description = "21 minute Just Ride"
        description, error = generate_description(workout)
        self.assertEqual(description, expected_description)
        self.assertIsNone(error)

    def test_regular_ride_description(self):
        """
        Test case to verify the description generated for a regular ride workout.
        """
        workout = {
            "ride": {
                "title": "20 min Climb Ride",
                "difficulty_estimate": 7.7326,
                "description": "There’s nothing more satisfying than leaving a hill in your dust.",
            },
            "instructor_name": "Emma Lovewell",
            "leaderboard_rank": 2375,
            "total_leaderboard_users": 10267,
            "ftp_info": {
                "ftp": 213
            }
        }
        expected_description = """Ride Title: 20 min Climb Ride
Difficulty: 7.7326
Leaderboard: 2375/10267 23.13%
FTP: 213
Description: There’s nothing more satisfying than leaving a hill in your dust."""
        description, error = generate_description(workout)
        self.assertEqual(description, expected_description)
        self.assertIsNone(error)

    def test_unknown_description(self):
        """
        Test case to verify we get an error back for an invalid workout.
        """
        workout = {"ride": {}, "instructor_name": "", "ftp_info": { "ftp": None }}
        expected_description = "Unknown Description"
        # Pass in silent=True to generate_description since we expect it to raise an exception
        description, error = generate_description(workout, True)
        self.assertEqual(description, expected_description)
        self.assertIsInstance(error, Exception)


if __name__ == '__main__':
    unittest.main()
