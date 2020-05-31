#!/usr/bin/env python3

'''
workouts_to_influxdb.py
Example usage of using pylotoncycle to pull in your workouts and import
them into influxdb.
'''

import argparse
import datetime
import pprint

import influxdb
import pylotoncycle


def ParseCommandLine():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n',
                        help='number of workouts',
                        dest='num_results',
                        action='store',
                        type=int,
                        default=10)
    parser.add_argument('--debug',
                        help='provide some debugging output',
                        dest='DEBUG',
                        action='store_true',
                        default=False)
    return parser


def ParseWorkout(workout_dict):
    # wt is short for 'workout tags'
    wt = {}

    # wf is short for 'workout fields'
    wf = {}

    w = workout_dict
    wt['fitness_discipline'] = w['fitness_discipline']
    # wt['created_at'] = w.created_at
    epoch_time = w['created_at']
    dt = datetime.datetime.fromtimestamp(epoch_time)
    created_at = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    wt['personal_record'] = w['is_total_work_personal_record']
    wt['status'] = w['status']
    try:
        wt['instructor'] = w['instructor_name']
    except KeyError:
        pass
    workout_duration_seconds = w['ride']['duration']
    workout_duration_minutes = workout_duration_seconds / 60
    wt['workout_duration_minutes'] = workout_duration_minutes
    wf['workout_duration_minutes'] = workout_duration_minutes
    ride_title = w['ride']['title']
    wf['workout_id'] = w['id']
    wf['title'] = ride_title
    if 'Groove Ride' in ride_title:
        wt['ride_type'] = 'Groove'
    elif 'Cool Down Ride' in ride_title:
        wt['ride_type'] = 'Cool Down'
    elif 'HIIT Ride' in ride_title:
        wt['ride_type'] = 'HIIT Ride'
    elif 'Power Zone' in ride_title:
        wt['ride_type'] = 'Power Zone'
    elif 'Sweat Steady Ride' in ride_title:
        wt['ride_type'] = 'Sweat Steady Ride'

    try:
        wf['cadence_max_rpm'] = w['overall_summary']['max_cadence']
        wf['cadence_average_rpm'] = w['overall_summary']['avg_cadence']
        wf['leaderboard_rank'] = w['leaderboard_rank']
        wf['num_leaderboard_users'] = w['total_leaderboard_users']
        wf['output_average_watts'] = w['overall_summary']['avg_power']
        wf['output_max_watts'] = w['overall_summary']['max_power']
        wf['resistance_max_percent'] = w['overall_summary']['max_resistance']
        wf['resistance_average_percent'] = \
            w['overall_summary']['avg_resistance']
        wf['speed_max'] = w['overall_summary']['max_speed']
        wf['speed_average'] = w['overall_summary']['avg_speed']
        wf['ftp'] = w['ftp_info']['ftp']

    except KeyError:
        pass

    return created_at, wt, wf


if __name__ == '__main__':
    parser = ParseCommandLine()
    args = parser.parse_args()
    DEBUG = args.DEBUG
    username = ''
    password = ''

    influxdb_hostname = 'localhost'
    influxdb_database = 'workouts'
    influxdb_username = ''
    influxdb_password = ''

    conn = pylotoncycle.PylotonCycle(username, password)

    workouts = conn.GetRecentWorkouts(num_workouts=args.num_results)

    client = influxdb.InfluxDBClient(
        influxdb_hostname,
        database=influxdb_database,
        username=influxdb_username,
        password=influxdb_password)

    data_points = []
    for w in workouts:
        pprint.pprint(w)
        created_at, wt, wf = ParseWorkout(w)
        json_body = [
            {
                'measurement': 'peloton_workouts',
                'tags': wt,
                'time': created_at,
                'fields': wf
            }
        ]
        if DEBUG:
            pprint.pprint(json_body)
        data_points.extend(json_body)
    print('Writing %s to database' % len(data_points))
    client.write_points(data_points)
