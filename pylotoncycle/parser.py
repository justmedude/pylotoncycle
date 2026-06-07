def ParseCyclingMetrics(json_resp):
    segment_dict = {}
    for seg in json_resp.get("segment_list", []):
        segment_name = seg["name"]
        start = seg["start_time_offset"]
        end = start + seg["length"]
        for sec in range(start, end):
            segment_dict[sec] = segment_name

    perf_dict = {}
    metrics_cached = [
        (m["slug"], m["values"]) for m in json_resp.get("metrics", [])
    ]
    seconds_since_pedaling_start_list = json_resp.get(
        "seconds_since_pedaling_start", []
    )

    for idx, seconds in enumerate(seconds_since_pedaling_start_list):
        entry = {}
        for slug, values in metrics_cached:
            entry[slug] = values[idx]
        entry["segment"] = segment_dict.get(seconds)
        perf_dict[seconds] = entry

    return perf_dict


def ParseOutdoorRunMetrics(json_resp):
    segment_dict = {
        seg["id"]: (seg["name"], seg["metrics_type"])
        for seg in json_resp.get("segment_list", [])
    }

    perf_dict = {}
    for location in json_resp.get("location_data", []):
        segment_info = segment_dict.get(location["segment_id"])
        if segment_info:
            segment_name, segment_metrics_type = segment_info
        else:
            segment_name = segment_metrics_type = None

        for coordinate in location.get("coordinates", []):
            offset = coordinate["seconds_offset_from_start"]
            coordinate["segment_name"] = segment_name
            coordinate["segment_metrics_type"] = segment_metrics_type
            perf_dict[offset] = coordinate

    return perf_dict
