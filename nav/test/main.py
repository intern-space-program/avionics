'''
File name: main.py
Programmed by: Mike Bernard
Date: 2020-03-05

This script runs all nav tests. It returns a 0 if no tests fail.
It otherwise returns the number of failed tests as an integer.
Descriptions of failed tests are printed to the terminal.
'''

# import test scripts here
import nav.test.NavMain_test as NavMain_test
import nav.test.NavMerge_test as NavMerge_test
import nav.test.frame_utils_test as frame_utils_test
import nav.test.quaternion_utils_test as quaternion_utils_test


class TestingError(Exception):
    pass


def main():
    '''
    The user needs to modify this function to include all modules
    they want to test.
    '''
    modules_to_test = [
        # add modules to test here
        NavMain_test,
        NavMerge_test,
        frame_utils_test,
        quaternion_utils_test
    ]

    print('-------- TEST RESULTS --------')

    run = 0
    failed = 0
    for module in modules_to_test:
        f, r = module.main()
        run += r
        failed += f

    print('---------- OVERALL -----------')
    print('Overall: {} of {} tests failed.'.format(failed, run))

    if failed == 0:
        print('Whoever wrote this is a genius.')

    else:
        raise TestingError('Changes from master have broken nav.')
    return failed


if __name__ == '__main__':
    main()
