'''
File name: common_utils.py
Programmed by: Mike Bernard
Date: 2019-11-08

Common helper functions used in multiple scripts.
'''

from nav.utils.constants import PASS


def weighted_avg(values, weights):
    '''
    Takes a list of values and a list of weights associated
    with those values (index-to-index) and returns a weighted
    averaged of those values as a float.

    :param values: `list` of values to be averaged
    :param weights: `list` of weights for each value (index-to-index)

    :return: `float` The weighted average of the values
    '''
    denom = sum([1 / w ** 2 for w in weights])
    num = sum([1 / w ** 2 * v for v, w in zip(values, weights)])

    return num / denom


def unit_test(module_name, tests):
    '''
    Run a set of test functions and print out the results.
    See test directory for examples of how to structure these tests
    and how to set up calling this function.
    
    :param module_name: `str` the name of the module being tested
    :param tests: `list` of functions to test as objects
    '''
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

    print(module_name, 'unit test results: ', end='')
    print('{} out of {} tests passed.'.format(passed, len(tests)))
    if failed > 0:
        print('{} failed tests:'.format(failed))
        for msg in fail_messages:
            print('\t' + msg)
    
    return failed
