"""
Parser utilities for Peloton workout metrics data.

Provides functions to transform raw API responses into more usable
data structures indexed by time.
"""


def ParseCyclingMetrics(json_resp):
    """
    Parse cycling workout metrics into a time-indexed dictionary.

    Transforms the raw performance graph API response into a dictionary
    keyed by seconds since pedaling start, with each entry containing
    all metric values and the current segment name.

    Args:
        json_resp: Raw JSON response from GetWorkoutMetricsById containing:
            - duration: Total workout duration in seconds
            - segment_list: List of workout segments with name, start_time_offset,
              and length
            - seconds_since_pedaling_start: List of time points
            - metrics: List of metric objects with slug and values

    Returns:
        dict: Dictionary keyed by seconds_since_pedaling_start, where each
            value is a dict containing metric values (cadence, output, etc.)
            and 'segment' indicating the current segment name.

    Example:
        >>> metrics = conn.GetWorkoutMetricsById(workout_id)
        >>> parsed = ParseCyclingMetrics(metrics)
        >>> parsed[60]  # Data at 60 seconds
        {'cadence': 85, 'output': 150, 'segment': 'Warmup'}
    """
    duration = json_resp["duration"]

    segment_dict = {}
    for i in range(0, duration + 1):
        segment_dict[i] = None

    for i in json_resp["segment_list"]:
        segment_name = i["name"]
        start_time_offset = i["start_time_offset"]
        end_time_offset = start_time_offset + i["length"]
        for j in range(start_time_offset, end_time_offset):
            segment_dict[j] = segment_name

    seconds_since_pedaling_start_list = json_resp[
        "seconds_since_pedaling_start"
    ]
    counter = 0

    perf_dict = {}
    for i in seconds_since_pedaling_start_list:
        seconds_since_pedaling_start = seconds_since_pedaling_start_list[
            counter
        ]

        perf_dict[seconds_since_pedaling_start] = {}
        for m in json_resp["metrics"]:
            slug = m["slug"]
            m_val = m["values"][counter]
            perf_dict[seconds_since_pedaling_start][slug] = m_val
            segment_name = segment_dict[seconds_since_pedaling_start]
            perf_dict[seconds_since_pedaling_start]["segment"] = segment_name
        counter += 1
    return perf_dict


def ParseOutdoorRunMetrics(json_resp):
    """
    Parse outdoor run metrics into a time-indexed dictionary.

    Transforms the raw performance graph API response for outdoor runs
    into a dictionary keyed by seconds since start, with GPS coordinates
    and segment information.

    Args:
        json_resp: Raw JSON response containing:
            - segment_list: List of segments with id, name, and metrics_type
            - location_data: List of segment data with coordinates

    Returns:
        dict: Dictionary keyed by seconds_offset_from_start, where each
            value contains the coordinate data plus segment_name and
            segment_metrics_type fields.

    Example:
        >>> metrics = conn.GetWorkoutMetricsById(outdoor_run_id)
        >>> parsed = ParseOutdoorRunMetrics(metrics)
        >>> parsed[120]  # Data at 2 minutes
        {'latitude': 40.7128, 'longitude': -74.0060,
         'segment_name': 'Run', 'segment_metrics_type': 'running'}
    """
    segment_list = json_resp["segment_list"]
    segment_dict = {}
    for i in segment_list:
        segment_id = i["id"]
        segment_name = i["name"]
        segment_metrics_type = i["metrics_type"]
        segment_dict[segment_id] = {
            "segment_name": segment_name,
            "segment_metrics_type": segment_metrics_type,
        }

    perf_dict = {}
    for i in json_resp["location_data"]:
        segment_id = i["segment_id"]
        segment_name = segment_dict[segment_id]["segment_name"]
        segment_metrics_type = segment_dict[segment_id][
            "segment_metrics_type"
        ]

        for datapoint in i["coordinates"]:
            seconds_offset_from_start = datapoint["seconds_offset_from_start"]
            perf_dict[seconds_offset_from_start] = datapoint
            perf_dict[seconds_offset_from_start][
                "segment_name"
            ] = segment_name
            perf_dict[seconds_offset_from_start][
                "segment_metrics_type"
            ] = segment_metrics_type

    return perf_dict
