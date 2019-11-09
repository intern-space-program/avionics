'''
Filename: NavMerge.py
Programmed by: Mike Bernard
Date: 2019-11-08

NavMerge takes in sensor data that has been formatted by
NavReceive and outputs data that has been merged to a
minimized state vector.
'''

import numpy as np
from nav.quaternion_utils import *
from nav.constants import *
from nav.common_utils import weighted_avg


def merge_accel(prev_position, accel_nc, accel_c):
    '''
    Merges the IMU's conservative acceleration measurement with
    a calculated conservative acceleration based on the IMU's
    non-conservative measurement and gravity.

    For parameter descriptions, see merge_main function.
    '''
    if norm(prev_position) != 0:
        a_1_calulated = accel_nc - G_E*prev_position/((norm(prev_position))**3)
        a_1_avg = 0.5*(a_1_calulated + accel_c)
    else:
        a_1_avg = accel_c

    return a_1_avg


def merge_position(prev_position, prev_velocity, dt, accel_merged, gps, altitude):
    '''
    Merges the propagated previous position, the new GPS
    position, and the altitude sensor measurements.

    For parameter descriptions, see merge_main function.
    '''
    p_new_calc = prev_position + prev_velocity*dt + 0.5*accel_merged*dt**2
    # TODO: add better weighting based on sensor error
    z_merged = weighted_avg(values=[altitude, gps[2]], weights=[1, 1])
    p_new_est = np.array([gps[0], gps[1], z_merged])

    return 0.5*(p_new_calc + p_new_est)


def merge_velocity(prev_velocity, dt, accel_merged):
    '''
    Merges the integrated IMU acceleration and the airspeed
    sensor velocity measurements into a less-errorful value.

    For parameter descriptions, see merge_main function.
    '''
    v_new = prev_velocity + accel_merged*dt

    # TODO: implement this if an airspeed sensor becomes available
    # std_imu = sigmas['IMU']
    # std_airspeed = sigmas['airspeed']
    # v_new_mag = norm(v_new)
    # v_new_mag_est = weighted_avg([v_new_mag, airspeed],
    #                              [std_imu, std_airspeed])
    #
    # return v_new_mag_est * v_new / v_new_mag

    return v_new


def merge_attitude(prev_attitude, current_attitude, delta_theta):
    '''
    Propagates the attitude based on the delta-angle change
    measured by the IMU. Assumes small angles only.

    :param prev_attitude: `np.array([1x4])` (--) A quaternion of the last known attitude
    :param current_attitude: `np.array([1x4])` (--) The IMU's estimate of the current attitude
    :param delta_theta: `np.array([1x3])` (rad) The IMU's delta-angle measurements
    '''
    dq_inert_to_body = norm(concatenate([np.array([1]), 0.5*delta_theta]))
    q_inert_to_body_new_calc = qcomp(prev_attitude, dq_inert_to_body)

    q_inert_to_body_new = 0.5*(current_attitude + q_inert_to_body_new_calc)

    return q_inert_to_body_new


def merge_main(prev_state, new_measurements):
    '''
    Manages the propagation forward in time from the last
    known state to the current time using sensor measurements.

    :param prev_state: `dict` The last known P, V, Att of the vehicle.
    :param new_measurements: `dict` The most recent sensor measurements.

    :return: `dict` The estimated current state of the vehicle.
    '''
    ### SETUP ###

    # unpack the previous state
    prev_time = prev_state['time']
    prev_position = prev_state['position']
    prev_velocity = prev_state['velocity']
    prev_attitude = prev_state['attitude']

    # unpack the sensor measurements
    dt = new_measurements['dt']  # `float` (s) since previous state
    # airspeed = new_measurements['airspeed']  # `float` (m/s) current airspeed (no airspeed sensor F2019)
    altitude = new_measurements['altitude']  # `float` (m) current altitude
    gps = new_measurements['gps']  # `np.array([1x3])` (m) GPS position vector
    delta_theta = new_measurements['delta_theta']  # `np.array([1x3])` (rad) delta-angle IMU reading
    accel_nc = new_measurements['accel_nc']  # `np.array([1x3])` (m/s**2) non-conservative acceleration
    accel_c = new_measurements['accel_c']  # `np.array([1x3])` (m/s**2) conservative acceleration
    q_inert_to_body = new_measurements['q_inert_to_body']  # `np.array([1x4])` (--) attitude quaternion

    ### PROPAGATION ###

    accel_merged = merge_accel(prev_position, accel_nc, accel_c)  # merge the acceleration measurements

    merged_vals = {
        'time': prev_time + dt,
        'position': merge_position(prev_position, prev_velocity, dt, accel_merged, gps, altitude),
        'velocity': merge_velocity(prev_velocity, dt, accel_merged),
        'attitude': merge_attitude(prev_attitude, q_inert_to_body, delta_theta)
    }

    return merged_vals
