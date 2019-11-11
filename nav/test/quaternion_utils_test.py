'''
File name: quaternion_utils_test.py
Programmed by: Mike Bernard
Date: 2019-11-09
'''

from numpy import array, allclose
from numpy.linalg import norm
from nav.quaternion_utils import *
from nav.common_utils import unit_test
from nav.constants import PASS, FAIL


def qcomp_test_null():
    # setup
    description = 'qcomp_test_null - Test qcomp with zeroed-out inputs'
    q1 = array([0.0, 0.0, 0.0, 0.0])
    q2 = array([0.0, 0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0, 0.0])

    # unit test
    ret = qcomp(q1, q2)

    # results
    if allclose(ret, exp, atol=0.001):
        return PASS, description
    else:
        return FAIL, description


def qcomp_test_values():
    # setup
    description = 'qcomp_test_values - Test qcomp with non-zero inputs'
    q1 = array([1.0, 0.0, 0.0, 0.0])
    q2 = array([0.5, 0.5, 0.5, 0.5])

    # expected results
    exp = array([0.5, 0.5, 0.5, 0.5])

    # unit test
    ret = qcomp(q1, q2)

    # results
    if allclose(ret, exp, atol=0.001):
        return PASS, description
    else:
        return FAIL, description


def qnorm_test_null():
    # setup
    description = 'qnorm_test_null - Test qnorm with zeroed-out input'
    q = array([0.0, 0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0, 0.0])

    # unit test
    ret = qnorm(q)

    # results
    if allclose(ret, exp, atol=0.001):
        return PASS, description
    else:
        return FAIL, description


def qnorm_test_values():
    # setup
    description = 'qnorm_test_null - Test qnorm with non-zero input'
    q = array([0.5, 0.0, 0.0, 0.0])

    # expected results
    exp = array([1.0, 0.0, 0.0, 0.0])

    # unit test
    ret = qnorm(q)

    # results
    if allclose(ret, exp, atol=0.001):
        return PASS, description
    else:
        return FAIL, description


def main():
    module_name = 'quaternion_utils.py'
    tests = [
        qnorm_test_null,
        qnorm_test_values,
        qcomp_test_null,
        qcomp_test_values
    ]

    unit_test(module_name, tests)


if __name__ == '__main__':
    main()
