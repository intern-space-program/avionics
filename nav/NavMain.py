'''
File name: NavMain.py
Programmed by: Mike Bernard
Date: 2019-11-09

Provides access to the main functionality of Nav.
'''

from nav.utils.frame_utils import lla_to_ecef
import nav.NavMerge
import nav.NavFilter


def main(prev_state, sensor_data):
    '''
    Manages entire navigation functionality from
    reception of raw sensor data to outputted
    navigation telemetry.

    :param prev_state: The last known state of the vehicle
    :type prev_state: `dict`
    :param sensor_data: The raw sensor measurements
    :type sensor_data: `dict
    :return: `dict` of updated navigation state telemetry
    '''
    # convert GPS from LLA to ECEF
    sensor_data['gps'] = lla_to_ecef(sensor_data['gps'])

    # merge the sensor data for this cycle and
    # propagate the previous state to the current time
    merge = nav.NavMerge.merge_main(prev_state, sensor_data)

    # TODO: return filtered data rather than just merged data once NavFilter complete
    # filter = nav.NavFilter.filter_main(merge)
    # return filter

    return merge
