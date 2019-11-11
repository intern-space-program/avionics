'''
Unit Tests for NavMerge.py

Programmed by: Mike Bernard
Date: 2019-11-05
'''

from numpy import array, concatenate, allclose
from numpy.linalg import norm
from nav.constants import PASS, FAIL
from nav.NavMerge import *


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
    if allclose(ret, exp, atol=0.001):
        return PASS, description
    else:
        return FAIL, description


def merge_accel_test_values():
    # setup
    description = 'merge_accel_test_values - Test merge_accel with non-zero inputs'
    prev_position = array([1.73205, 1.73205, 1.73205])
    accel_nc = array([0.0, 0.0, 0.0])
    accel_c = array([0.0, 0.0, 0.0])

    # expected results
    # TODO convert this from a calculation to actual numbers
    new_a = 0.5*(-G_E*prev_position/((norm(prev_position))**3))
    exp = new_a

    # unit test
    ret = merge_accel(prev_position, accel_nc, accel_c)

    # results
    if allclose(ret, exp, atol=0.01):
        return PASS, description
    else:
        return FAIL, description


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
    if allclose(ret, exp, atol=0.001):
        return PASS, description
    else:
        return FAIL, description


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
    if allclose(ret, exp, atol=0.01):
        return PASS, description
    else:
        return FAIL, description


def merged_velocity_test():
    pass


def merge_attitude_test():
    pass


def merge_main_test():
    pass


# Test Loop
def main():
    tests = [
        merge_accel_test_null,
        merge_accel_test_values,
        merge_position_test_null,
        merge_position_test_values
    ]

    passed = 0
    failed = 0
    fail_messages = []

    for test in tests:
        status, description = test()
        if status == PASS:
            passed += 1
        else:
            failed += 1
            fail_messages.append(description)

    print('{} out of {} tests passed.'.format(passed, len(tests)))
    if len(fail_messages) > 0:
        print('Failed tests:')
        for msg in fail_messages:
            print('\t' + msg)


if __name__ == '__main__':
    main()
