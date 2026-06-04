import argparse
import csv
import os
from pathlib import Path

from pylotoncycle import PylotonCycle


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download Peloton workout history as a CSV file."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Directory where workouts.csv should be written.",
    )
    parser.add_argument(
        "--timezone",
        default="America/New_York",
        help="Timezone for the workout history CSV export.",
    )
    return parser.parse_args()


def GetWorkoutCSV(
    connection: PylotonCycle,
    path: str = ".",
    timezone: str = "America/New_York",
) -> dict:
    workouts_url = f"{connection.base_url}/api/user/{connection.userid}/workout_history_csv?timezone={timezone}"
    resp = connection.s.get(workouts_url, timeout=10)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to download workouts CSV: HTTP {resp.status_code}"
        )

    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir.joinpath("workouts.csv")

    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        for row in csv.reader(resp.text.splitlines()):
            writer.writerow(row)
            row_count += 1

    if row_count == 0:
        raise RuntimeError("Downloaded workouts CSV was empty.")

    print(f"Workouts saved to {output_path}")
    return {"response": resp, "path": output_path, "row_count": row_count}


def main():
    args = parse_args()
    username = os.environ.get("PELOTON_USERNAME")
    password = os.environ.get("PELOTON_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "Set PELOTON_USERNAME and PELOTON_PASSWORD before running."
        )

    conn = PylotonCycle(username, password)
    result = GetWorkoutCSV(
        connection=conn,
        path=args.path,
        timezone=args.timezone,
    )
    print(f"Downloaded {result['row_count']} CSV rows.")


if __name__ == "__main__":
    main()
