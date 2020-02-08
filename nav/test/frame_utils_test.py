'''
File name: frame_utils_test.py
Programmed by: Mike Bernard
Date: 2020-02-08

Unit tests for frame_utils.py.
'''

from numpy import allclose, array
from nav.utils.frame_utils import *
from nav.utils.common_utils import unit_test
from nav.utils.constants import PASS, FAIL


def lla_to_ecef_test_null():
    # setup
    description = 'lla_to_ecef_test_null - Test lla_to_ecef with zeroed-out inputs.'
    lla_array = array([0.0, 0.0, 0.0])

    # expected results
    exp = array([radius_equatorial, 0.0, 0.0])

    # unit test
    ret = lla_to_ecef(lla_array)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)

def lla_to_ecef_test_values():
    # setup
    description = 'lla_to_ecef_test_values - Test lla_to_ecef with flight-like inputs.'
    lla_array = array([29.5593, 95.0900, 304.8])  # 1000 ft above JSC!

    # expected results
    exp = array([-492646.0, 5530891.07, 3128126.477])  # approximate, but good enough for testing

    # unit test
    ret = lla_to_ecef(lla_array)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)

def main():
    module_name = 'frame_utils_test.py'
    tests = [
        lla_to_ecef_test_null,
        lla_to_ecef_test_values
    ]

    unit_test(module_name, tests)


if __name__ == '__main__':
    main()
