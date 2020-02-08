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
    desc = 'lla_to_ecef_test_null - Test lla_to_ecef with zeroed-out inputs.'
    lla_array = array([0.0, 0.0, 0.0])

    # expected results


    # unit test


    # results


def lla_to_ecef_test_values():
    # setup
    desc = 'lla_to_ecef_test_values - Test lla_to_ecef with flight-like inputs.'


def main():
    module_name = 'frame_utils_test.py'
    tests = [
        lla_to_ecef_test_null,
        lla_to_ecef_test_values
    ]

    unit_test(module_name, tests)


if __name__ == '__main__':
    main()
