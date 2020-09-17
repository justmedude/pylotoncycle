# PylotonCycle
Python Library for getting your Peloton workout data.

## Table of contents
* [General info](#general-info)
* [Example Usage](#example-usage)

## General info
As someone who wants to see my progress over time, I've been wanting a way
to pull and play with my ride data. However, I'm also cautious about linking
myself to too many external parties. As I've been playing with other libraries
out there, I wanted something that was a bit more intuitive and would play
nicer with the rest of my python code. So, PylotonCycle is born.

## Example Usage
```
import pylotoncycle

username = 'your username or email address'
password = 'your password'
conn = pylotoncycle.PylotonCycle(username, password)
workouts = conn.GetRecentWorkouts(5)
```
`workouts` is a list of workouts.

An example of a list element

```
{'achievement_templates': [{'description': 'Awarded for working out with a '
                                           'friend.',
                            'id': '<some id hash>',
                            'image_url': 'https://s3.amazonaws.com/peloton-achievement-images-prod/702495cd985d4791bfd3d25f36e0df72',
                            'name': 'Dynamic Duo',
                            'slug': 'two_to_tango'},
                           {'description': 'Awarded for achieving Silver in '
                                           'the May Cycling Challenge.',
                            'id': '<some id hash>',
                            'image_url': 'https://s3.amazonaws.com/challenges-and-tiers-image-prod/6b772477ccd04f189fba16f2f877faad',
                            'name': 'May Cycling Challenge',
                            'slug': 'may_cycling_challenge_silver'}],
 'created': 1589642476,
 'created_at': 1589642476,
 'device_time_created_at': 1589617276,
 'device_type': 'home_bike_v1',
 'device_type_display_name': 'Bike',
 'end_time': 1589644336,
 'fitbit_id': None,
 'fitness_discipline': 'cycling',
 'ftp_info': {'ftp': 111,
              'ftp_source': 'ftp_workout_source',
              'ftp_workout_id': '<some id hash>'},
 'has_leaderboard_metrics': True,
 'has_pedaling_metrics': True,
 'id': '<some id hash>',
 'instructor_name': 'Matt Wilpers',
 'is_total_work_personal_record': False,
 'leaderboard_rank': 5015,
 'metrics_type': 'cycling',
 'name': 'Cycling Workout',
 'overall_summary': {'avg_cadence': 85.48,
                     'avg_heart_rate': 0.0,
                     'avg_power': 179.24,
                     'avg_resistance': 47.61,
                     'avg_speed': 20.39,
                     'cadence': 0.0,
                     'calories': 496.71,
                     'distance': 10.19,
                     'heart_rate': 0.0,
                     'id': '<some id hash>',
                     'instant': 1589644336,
                     'max_cadence': 122.0,
                     'max_heart_rate': 0.0,
                     'max_power': 255.8,
                     'max_resistance': 60.95,
                     'max_speed': 23.48,
                     'power': 0.0,
                     'resistance': 0.0,
                     'seconds_since_pedaling_start': 0,
                     'speed': 0.0,
                     'total_work': 322417.21,
                     'workout_id': '<some id hash>'},
 'peloton_id': '<some id hash>',
 'platform': 'home_bike',
 'ride': {'captions': ['en-US'],
          'class_type_ids': ['<some id hash>'],
          'content_format': 'video',
          'content_provider': 'peloton',
          'description': 'Max out the effectiveness of your training with this '
                         'ride. Instructors will expertly guide you through '
                         'specific output ranges 1 through 7 to help you build '
                         'endurance, strength and speed.',
          'difficulty_estimate': 6.3779,
          'difficulty_level': None,
          'difficulty_rating_avg': 6.3779,
          'difficulty_rating_count': 17157,
          'duration': 1800,
          'equipment_ids': [],
          'equipment_tags': [],
          'excluded_platforms': [],
          'extra_images': [],
          'fitness_discipline': 'cycling',
          'fitness_discipline_display_name': 'Cycling',
          'has_closed_captions': True,
          'has_free_mode': False,
          'has_pedaling_metrics': True,
          'home_peloton_id': '<some id hash>',
          'id': '<some id hash>',
          'image_url': 'https://s3.amazonaws.com/peloton-ride-images/58aa8ebc7d51d09d6513e1a2fab53c4c62c076c6/img_1580922399_a5f1fd0e3a2e48d38ecdd6a3d874820f.png',
          'instructor_id': '<some id hash>',
          'is_archived': True,
          'is_closed_caption_shown': True,
          'is_explicit': False,
          'is_live_in_studio_only': False,
          'language': 'english',
          'length': 1940,
          'live_stream_id': '<some id hash>-live',
          'live_stream_url': None,
          'location': 'nyc',
          'metrics': ['heart_rate', 'cadence', 'calories'],
          'origin_locale': 'en-US',
          'original_air_time': 1580919480,
          'overall_estimate': 0.9956,
          'overall_rating_avg': 0.9956,
          'overall_rating_count': 20737,
          'pedaling_duration': 1800,
          'pedaling_end_offset': 1860,
          'pedaling_start_offset': 60,
          'rating': 0,
          'ride_type_id': '<some id hash>',
          'ride_type_ids': ['<some id hash>'],
          'sample_vod_stream_url': None,
          'scheduled_start_time': 1580920200,
          'series_id': '<some id hash>',
          'sold_out': False,
          'studio_peloton_id': '<some id hash>',
          'title': '30 min Power Zone Endurance Ride',
          'total_in_progress_workouts': 0,
          'total_ratings': 0,
          'total_workouts': 32489,
          'vod_stream_id': '<some id hash>-vod',
          'vod_stream_url': None},
 'start_time': 1589642537,
 'status': 'COMPLETE',
 'strava_id': None,
 'timezone': 'America/Los_Angeles',
 'title': None,
 'total_leaderboard_users': 31240,
 'total_work': 322417.21,
 'user_id': '<some id hash>',
 'workout_type': 'class'}
```

An example of how you may fetch performance data for a ride
```
import pprint

conn = pylotoncycle.PylotonCycle(username, password)
workouts = conn.GetRecentWorkouts(5)
for w in workouts:
    workout_id = w['id']
    resp = conn.GetWorkoutMetricsById(workout_id)
    pprint.pprint(resp)

```

## Install
This package is available via pip install.
```
pip install pylotoncycle
```

## TODO
* Lots more to cover. I want to find the right format for pulling in the
ride performance data.
* Pull in GPS data for outdoor runs
