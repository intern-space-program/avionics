'''
File name: NavMerge_test.py
Programmed by: Mike Bernard
Date: 2019-11-05

Unit tests for NavMerge.py.
'''

from numpy import array, allclose
from numpy.linalg import norm
from nav.NavMerge import *
from nav.utils.common_utils import unit_test
from nav.utils.constants import PASS, FAIL


def merge_accel_test_null():
    # setup
    description = 'merge_accel_test_null - Test merge_accel with zeroed-out inputs'
    prev_position = array([0.0, 0.0, 0.0])
    accel_nc = array([0.0, 0.0, 0.0])
    accel_c = array([0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0])

    # unit test
    ret = merge_accel(prev_position, accel_nc, accel_c)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def merge_accel_test_values():
    # setup
    description = 'merge_accel_test_values - Test merge_accel with non-zero inputs'
    prev_position = array([0.0, 0.0, 6371000.0])
    accel_nc = array([1.0, 1.0, 0.0])
    accel_c = array([1.0, 1.0, -G_E/6371000**2])

    # expected results
    exp = array([1.0, 1.0, 0.0])

    # unit test
    ret = merge_accel(prev_position, accel_nc, accel_c)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def merge_position_test_null():
    # setup
    description = 'merge_position_test_null - Test merge_position with zeroed-out inputs'
    prev_position = array([0.0, 0.0, 0.0])
    prev_velocity = array([0.0, 0.0, 0.0])
    dt = 0.0
    accel_merged = array([0.0, 0.0, 0.0])
    gps = array([0.0, 0.0, 0.0])
    altitude = 0.0

    # expected results
    exp = array([0.0, 0.0, 0.0])

    # unit test
    ret = merge_position(prev_position, prev_velocity, dt, accel_merged, gps, altitude)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def merge_position_test_values():
    # setup
    description = 'merge_position_test_values - Test merge_position with non-zero inputs'
    prev_position = array([1.0, 1.0, 1.0])
    prev_velocity = array([1.0, 1.0, 1.0])
    dt = 0.1
    accel_merged = array([5.0, 5.0, 5.0])
    gps = array([1.2, 1.2, 1.2])
    altitude = 1.1

    # expected results
    exp = array([1.1625, 1.1625, 1.1375])

    # unit test
    ret = merge_position(prev_position, prev_velocity, dt, accel_merged, gps, altitude)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def merge_velocity_test_null():
    # setup
    description = 'merge_velocity_test_null - Test merge_velocity with zeroed-out inputs'
    prev_velocity = array([0.0, 0.0, 0.0])
    dt = 0.0
    accel_merged = array([0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0])

    # unit test
    ret = merge_velocity(prev_velocity, dt, accel_merged)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def merge_velocity_test_values():
    # setup
    description = 'merge_velocity_test_null - Test merge_velocity with non-zero inputs'
    prev_velocity = array([1.0, 1.0, 1.0])
    dt = 0.1
    accel_merged = array([10.0, 10.0, 10.0])

    # expected results
    exp = array([2.0, 2.0, 2.0])

    # unit test
    ret = merge_velocity(prev_velocity, dt, accel_merged)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def merge_attitude_test():
    # setup
    description = 'merge_attitude_test - Test merge_attitude function with an input (F2019 version just returns the input)'
    prev_attitude = array([1.0, 0.0, 0.0, 0.0])
    current_attitude = array([0.9999619, 0, 0, 0.0087265])
    delta_theta = array([0, 0, 0.0174533])  # 1 degree rotation about z-axis

    # expected results
    exp = array([0.9999619, 0, 0, 0.0087265])

    # unit test
    ret = merge_attitude(prev_attitude, current_attitude, delta_theta)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)

def merge_main_test():
    '''
    This test is covered by the overall integration test found in
    NavMain_test.py.
    '''
    pass


# Test Loop
def main():
    module_name = 'NavMerge.py'
    
    tests = [
        merge_accel_test_null,
        merge_accel_test_values,
        merge_position_test_null,
        merge_position_test_values,
        merge_velocity_test_null,
        merge_velocity_test_values,
        merge_attitude_test
    ]

    num_tests = len(tests)
    failed = unit_test(module_name, tests)
    return failed, num_tests


if __name__ == '__main__':
    main()
