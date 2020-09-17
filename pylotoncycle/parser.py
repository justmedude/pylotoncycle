def ParseCyclingMetrics(json_resp):
    duration = json_resp['duration']

    # Initialize a fast lookup dictionary to map seconds of the ride
    # to a segment.
    # The format of the dictionary is:
    # seconds_since_pedaling_start : segment_name
    # Initially, we know the duration of the ride, so we use that and init
    # all segments as None
    segment_dict = {}
    for i in range(0, duration + 1):
        segment_dict[i] = None

    # Now, for every segment that is listed, we want to map into segment_dict
    # what the name of that segment is.
    for i in json_resp['segment_list']:
        segment_name = i['name']
        start_time_offset = i['start_time_offset']
        end_time_offset = start_time_offset + i['length']
        # Using our start and end times, map into the segment_dict what
        # segment name each second corresponds to
        for j in range(start_time_offset, end_time_offset):
            segment_dict[j] = segment_name

    seconds_since_pedaling_start_list = \
        json_resp['seconds_since_pedaling_start']
    counter = 0

    perf_dict = {}
    for i in seconds_since_pedaling_start_list:
        seconds_since_pedaling_start = \
            seconds_since_pedaling_start_list[counter]

        perf_dict[seconds_since_pedaling_start] = {}
        for m in json_resp['metrics']:
            slug = m['slug']
            m_val = m['values'][counter]
            perf_dict[seconds_since_pedaling_start][slug] = m_val
            segment_name = segment_dict[seconds_since_pedaling_start]
            perf_dict[seconds_since_pedaling_start]['segment'] = segment_name
        counter += 1
    return perf_dict


def ParseOutdoorRunMetrics(json_resp):
    # duration = json_resp['duration']

    segment_list = json_resp['segment_list']
    segment_dict = {}
    for i in segment_list:
        segment_id = i['id']
        segment_name = i['name']
        segment_metrics_type = i['metrics_type']
        segment_dict[segment_id] = {
            'segment_name': segment_name,
            'segment_metrics_type': segment_metrics_type
        }

    perf_dict = {}
    for i in json_resp['location_data']:
        segment_id = i['segment_id']
        segment_name = segment_dict[segment_id]['segment_name']
        segment_metrics_type = segment_dict[segment_id]['segment_metrics_type']

        for datapoint in i['coordinates']:
            seconds_offset_from_start = datapoint['seconds_offset_from_start']
            perf_dict[seconds_offset_from_start] = datapoint
            perf_dict[seconds_offset_from_start]['segment_name'] = segment_name
            perf_dict[seconds_offset_from_start]['segment_metrics_type'] = \
                segment_metrics_type

    return perf_dict
