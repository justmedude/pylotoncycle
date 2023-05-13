#!/usr/bin/env python3

"""
workouts_to_ics.py
Example usage of using pylotoncycle to pull in your workouts and output
them to a ICS iCalendar (RFC 2445) file.
"""
import os
import sys
import traceback
import argparse
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pylotoncycle

def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', help='Peloton username')
    parser.add_argument('--password', help='Peloton password')
    parser.add_argument('--num_results', type=int, default=10, help='Number of recent workouts to fetch')
    parser.add_argument('--input_json', help='Path to input JSON file containing workouts')
    parser.add_argument('--output_json', help='Path to output JSON file for the fetched workouts')
    parser.add_argument('--calendar_name', default='Peloton Workouts', help='Calendar name')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()


def generate_description(workout):
    ride = workout['ride']
    leaderboard_rank = workout.get('leaderboard_rank', 'N/A')
    total_leaderboard_users = workout.get('total_leaderboard_users', 'N/A')
    ftp = workout['ftp_info'].get('ftp', 'N/A')

    instructor_name = workout['instructor_name']
    try:
        if instructor_name == "JUST RIDE":
            workout_len = workout['ride']['duration'] // 60
            description = f"{workout_len} minute Just Ride"
        else:
            description = f"Ride Title: {ride.get('title', 'N/A')}\n"
            description += f"Difficulty: {ride.get('difficulty_estimate', 'N/A')}\n"
            if leaderboard_rank != 0 and total_leaderboard_users:
                percentile = leaderboard_rank / total_leaderboard_users * 100
                description += f"Leaderboard: {leaderboard_rank}/{total_leaderboard_users} {percentile:.2f}%\n"
            description += f"FTP: {ftp}\n"
            description += f"Description: {ride.get('description', 'N/A')}"
        return description, None
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        traceback.print_exc()
        return "Unknown Description", err


def convert_to_ical(workouts, calendar_name='Peloton Workouts'):
    cal = Calendar()
    cal.add('VERSION', '2.0')
    cal.add('PRODID', '-//pylotoncycle workouts_to_ics.py//EN')
    cal.add('X-WR-CALNAME', calendar_name)

    for workout in workouts:
        created_at = datetime.fromtimestamp(int(workout['created_at']))
        end_time = created_at + timedelta(minutes=workout['ride']['duration'] // 60)
        workout_type = workout['fitness_discipline']
        ride = workout['ride']
        workout_title = ride.get('title', 'Untitled')
        instructor_name = workout['instructor_name']
        if instructor_name == "JUST RIDE":
            workout_len = workout['ride']['duration'] // 60
            title = f"{workout_len} minute Just Ride"
        else:
            title = f"{workout_title} with {instructor_name}"

        start_time = created_at
        end_time = created_at + timedelta(minutes=workout['ride']['duration'] // 60)

        event = Event()
        # Add image as ATTACH if there is one
        image_url = ride.get('image_url', None)
        if image_url:
            event.add('attach', image_url)
        event.add('summary', title.encode('utf-8'))
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        description, err = generate_description(workout)
        event.add('description', description.encode('utf-8'))

        cal.add_component(event)

    ical_data = cal.to_ical().decode('utf-8')

    return ical_data


if __name__ == "__main__":
    args = parse_command_line()
    debug_mode = args.debug

    username = args.username or os.environ.get('PELOTON_USERNAME')
    password = args.password or os.environ.get('PELOTON_PASSWORD')
    input_json = args.input_json
    output_json = args.output_json

    if input_json:
        with open(input_json) as f:
            workouts = json.load(f)
    else:
        if not username or not password:
            raise ValueError("Peloton username and password are required.")
        print("Attempting to connect...", file=sys.stderr))
        conn = pylotoncycle.PylotonCycle(username, password)
        print("Connected.", file=sys.stderr))
        workouts = conn.GetRecentWorkouts(num_workouts=args.num_results)

    if output_json:
        with open(output_json, 'w') as f:
            json.dump(workouts, f, indent=4)

    ical_data = convert_to_ical(workouts, calendar_name=args.calendar_name)

    # Print the generated iCalendar data to stdout
    print(ical_data)

