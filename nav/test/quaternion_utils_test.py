'''
File name: quaternion_utils_test.py
Programmed by: Mike Bernard
Date: 2019-11-09

Unit tests for quaternion_utils.py.
'''

from numpy import allclose
from nav.utils.quaternion_utils import *
from nav.utils.common_utils import unit_test
from nav.utils.constants import PASS, FAIL


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
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


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
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qnorm_test_null():
    # setup
    description = 'qnorm_test_null - Test qnorm with zeroed-out input'
    q = array([0.0, 0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0, 0.0])

    # unit test
    ret = qnorm(q)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qnorm_test_values():
    # setup
    description = 'qnorm_test_null - Test qnorm with non-zero input'
    q = array([0.5, 0.0, 0.0, 0.0])

    # expected results
    exp = array([1.0, 0.0, 0.0, 0.0])

    # unit test
    ret = qnorm(q)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qvectransform_test_null1():
    # setup
    description = 'qvectransform_test_null1 - Test qvectransform with zeroed-out inputs'
    q = array([0.0, 0.0, 0.0, 0.0])
    v = array([0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0])

    # unit test
    ret = qvectransform(q, v)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qvectransform_test_null2():
    # setup
    description = 'qvectransform_test_null2 - Test qvectransform with transform quaternion, zeroed-out vector'
    q = array([0.70710678, 0.0, 0.70710678, 0.0])  # rotate about y-axis by pi/2 rad
    v = array([0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0])

    # unit test
    ret = qvectransform(q, v)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qvectransform_test_null3():
    # setup
    description = 'qvectransform_test_null3 - Test qvectransform with zeroed-out quaternion, non-zero vector'
    q = array([0.0, 0.0, 0.0, 0.0])
    v = array([1.0, 1.0, 1.0])

    # expected results
    exp = array([0.0, 0.0, 0.0])

    # unit test
    ret = qvectransform(q, v)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qvectransform_test_values1():
    # setup
    description = 'qvectransform_test_values1 - Test qvectransform with scalar quaternion'
    q = array([1.0, 0.0, 0.0, 0.0])
    v = array([10.0, 5.0, 1.0])

    # expected results
    exp = array([10.0, 5.0, 1.0])

    # unit test
    ret = qvectransform(q, v)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qvectransform_test_values2():
    # setup
    description = 'qvectransform_test_values2 - Test qvectransform with transform quaternion'
    q = array([0.70710678, 0.0, 0.70710678, 0.0])  # rotate about y-axis by pi/2 rad
    v = array([1.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 1.0])

    # unit test
    ret = qvectransform(q, v)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qvectransform_test_values3():
    # setup
    description = 'qvectransform_test_values3 - Test qvectransform with transform quaternion'
    q = array([0.5, 0.5, 0.5, 0.5])  # rotate about [1, 1, 1] by 2*pi/3 rad
    v = array([0.0, 1.0, 0.0])

    # expected results
    exp = array([1.0, 0.0, 0.0])

    # unit test
    ret = qvectransform(q, v)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qconjugate_test_null():
    # setup
    description = 'qconjugate_test_null - Test qconjugate with zeroed-out input'
    q = array([0.0, 0.0, 0.0, 0.0])

    # expected results
    exp = array([0.0, 0.0, 0.0, 0.0])

    # unit test
    ret = qconjugate(q)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def qconjugate_test_values():
    # setup
    description = 'qconjugate_test_null - Test qconjugate with non-zero input'
    q = array([0.5, 0.5, 0.5, 0.5])

    # expected results
    exp = array([0.5, -0.5, -0.5, -0.5])

    # unit test
    ret = qconjugate(q)

    # results
    return (PASS, description) if allclose(ret, exp, atol=0.001) \
        else (FAIL, description)


def main():
    module_name = 'quaternion_utils.py'
    tests = [
        qnorm_test_null,
        qnorm_test_values,
        qcomp_test_null,
        qcomp_test_values,
        qvectransform_test_null1,
        qvectransform_test_null2,
        qvectransform_test_null3,
        qvectransform_test_values1,
        qvectransform_test_values2,
        qvectransform_test_values3,
        qconjugate_test_null,
        qconjugate_test_values
    ]

    num_tests = len(tests)
    failed = unit_test(module_name, tests)
    return failed, num_tests


if __name__ == '__main__':
    main()
