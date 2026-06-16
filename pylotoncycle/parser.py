from typing import Any, Dict


def ParseCyclingMetrics(
    json_resp: Dict[str, Any],
) -> Dict[int, Dict[str, Any]]:
    """Parses cycling workout metrics from the Peloton API response.

    Args:
        json_resp: The raw JSON response from the workout performance graph endpoint.

    Returns:
        A dictionary keyed by seconds since start, containing metrics for that second.

    Raises:
        KeyError: If required fields are missing from the response.
    """
    # Ensure fail-fast behavior on missing required fields from the API payload
    for key in (
        "duration",
        "segment_list",
        "metrics",
        "seconds_since_pedaling_start",
    ):
        if key not in json_resp:
            raise KeyError(key)

    duration = json_resp["duration"]
    segment_dict = {}
    for seg in json_resp["segment_list"]:
        segment_name = seg["name"]
        start = seg["start_time_offset"]
        end = start + seg["length"]
        for sec in range(start, end):
            segment_dict[sec] = segment_name

    perf_dict = {}
    metrics_cached = [(m["slug"], m["values"]) for m in json_resp["metrics"]]
    seconds_since_pedaling_start_list = json_resp[
        "seconds_since_pedaling_start"
    ]

    for idx, seconds in enumerate(seconds_since_pedaling_start_list):
        # Validate that seconds are within range 0..duration
        # to preserve KeyError on out-of-bounds samples
        if not (0 <= seconds <= duration):
            raise KeyError(seconds)

        entry = {}
        if metrics_cached:
            for slug, values in metrics_cached:
                entry[slug] = values[idx]
            entry["segment"] = segment_dict.get(seconds)
        perf_dict[seconds] = entry

    return perf_dict


def ParseOutdoorRunMetrics(
    json_resp: Dict[str, Any],
) -> Dict[int, Dict[str, Any]]:
    """Parses outdoor run metrics from the Peloton API response.

    Args:
        json_resp: The raw JSON response from the workout performance graph endpoint.

    Returns:
        A dictionary keyed by seconds offset, containing location and metrics data.

    Raises:
        KeyError: If required fields are missing from the response.
    """
    # Ensure fail-fast behavior on missing required fields from the API payload
    for key in ("segment_list", "location_data"):
        if key not in json_resp:
            raise KeyError(key)

    segment_dict = {
        seg["id"]: (
            seg["name"],
            seg["metrics_type"],
        )
        for seg in json_resp["segment_list"]
    }

    perf_dict = {}
    for location in json_resp["location_data"]:
        segment_name, segment_metrics_type = segment_dict[
            location["segment_id"]
        ]

        for coordinate in location["coordinates"]:
            offset = coordinate["seconds_offset_from_start"]
            coordinate["segment_name"] = segment_name
            coordinate["segment_metrics_type"] = segment_metrics_type
            perf_dict[offset] = coordinate

    return perf_dict
