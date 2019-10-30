from nav.NavIO import json_to_dict, dict_to_json
from nav.NavMerge import NavMerge
import nav.NavFilter


def NavMain(prev_state, sensor_data):
    '''
    Manages entire navigation functionality from
    reception of raw sensor data to outputted
    navigation telemetry.

    :param sensor_data: The raw sensor measurements
    :type sensor_data: TODO
    :return: `dict` of updated navigation state telemetry
    '''
    decoded_data = json_to_dict(sensor_data)

    merge_inputs = nav.NavMerge.decoded_data_to_merge_inputs(prev_state, decoded_data)
    nav_merge = NavMerge(*merge_inputs)
    merged_data = nav_merge.merged_vals

    nav_filter = NavFilter(merged_data)
    filtered_data = nav_filter.filtered_vals

    encoded_data = dict_to_json(filtered_data)

    return encoded_data
