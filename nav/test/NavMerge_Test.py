'''
Unit Tests for NavMerge.py

Programmed by: Mike Bernard
Date: 2019-11-05
'''

def weighted_avg_test():
    pass


def merge_position_test():
    pass


def integrate_imu_linear_test():
    pass


def merge_velocity_test():
    pass


def merged_accel_test():
    pass


def attitude_test():
    pass


def init_test():
    pass


# Test Loop
def main():
    test_order = [
        "weighted_avg",
        "merge_position",
        "integrate_imu_linear",
        "merge_velocity",
        "merged_accel",
        "attitude",
        "__init__"
    ]

    test_functions = {
        # unit tests
        'weighted_avg': weighted_avg_test,
        'merge_position': merge_position_test,
        'integrate_imu_linear': integrate_imu_linear_test,
        'merge_velocity': merge_velocity_test,
        'merged_accel': merged_accel_test,
        'attitude': attitude_test,

        # "integration" test
        '__init__': init_test
    }

    statuses = {}
    passed = 0
    failed = 0

    for name, test in test_functions.items():
        status = test()  # 0 = pass, 1 = fail
        statuses[name] = status
        if status:
            failed += 1
        else:
            passed += 1

    for test, status in statuses.items():
        if status == 1:
            print('Test Failed: {}'.format(test))


if __name__ == '__main__':
    main()
