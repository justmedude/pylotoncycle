import unittest
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from workouts_to_ics import generate_description, convert_to_ical


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



class TestConvertToICal(unittest.TestCase):

    def test_convert_to_ical_regular_ride(self):
        """
        Test case to verify the conversion of a regular ride workout to iCalendar format.
        """
        workout = {
            "created_at": 1672946636,
            "ride": {
                "title": "20 min Climb Ride",
                "duration": 1273,
                "instructor": {
                    "name": "Emma Lovewell"
                }
            },
            "instructor_name": "Emma Lovewell",
            "fitness_discipline": "cycling",
            "leaderboard_rank": 2375,
            "total_leaderboard_users": 10267,
            "ftp_info": {
                "ftp": 213
            }
        }

        expected_ical_data = self._generate_expected_ical_data(workout)

        workouts = [workout]
        ical_data = convert_to_ical(workouts)

        self.assertEqual(ical_data, expected_ical_data)

    def test_convert_to_ical_just_ride(self):
        """
        Test case to verify the conversion of a 'Just Ride' workout to iCalendar format.
        """
        workout = {
            "created_at": 1672946636,
            "ride": {
                "title": "21 min Just Ride",
                "duration": 1273,
                "instructor": {
                    "name": "JUST RIDE"
                }
            },
            "instructor_name": "JUST RIDE",
            "fitness_discipline": "cycling",
            "ftp_info": {
                "ftp": None,
                "ftp_source": None,
                "ftp_workout_id": None
            }
        }

        expected_ical_data = self._generate_expected_ical_data(workout)

        workouts = [workout]
        ical_data = convert_to_ical(workouts)

        self.assertEqual(ical_data, expected_ical_data)

    def _generate_expected_ical_data(self, workout):
        """
        Generate the expected iCalendar data for a given workout.

        Args:
            workout (dict): The workout data.

        Returns:
            str: The expected iCalendar data.
        """
        cal = Calendar()
        cal.add('VERSION', '2.0')
        cal.add('PRODID', '-//pylotoncycle workouts_to_ics.py//EN')
        cal.add('X-WR-CALNAME', 'Peloton Workouts')

        created_at = datetime.fromtimestamp(int(workout['created_at']))
        end_time = created_at + timedelta(minutes=workout['ride']['duration'] // 60)
        workout_title = workout['ride'].get('title', 'Untitled')
        instructor_name = workout['instructor_name']

        if instructor_name == "JUST RIDE":
            workout_len = workout['ride']['duration'] // 60
            title = f"{workout_len} minute Just Ride"
        else:
            title = f"{workout_title} with {instructor_name}"

        event = Event()
        event.add('summary', title.encode('utf-8'))
        event.add('dtstart', created_at)
        event.add('dtend', end_time)

        description, _ = generate_description(workout)
        event.add('description', description.encode('utf-8'))

        cal.add_component(event)
        expected_ical_data = cal.to_ical().decode('utf-8')

        return expected_ical_data


if __name__ == '__main__':
    unittest.main()
