'''
File name: NavMain_test.py
Programmed by: Mike Bernard
Date: 2019-11-05

This is a unit test of the nav_main function.
This also serves as an effective integration test for
the Nav design for F2019.
'''

from numpy import array, allclose, arange, zeros
from numpy.linalg import norm
from nav.utils.frame_utils import lla_to_ecef, ecef_to_lla
from nav.utils.common_utils import unit_test
from nav.utils.constants import PASS, FAIL, G_E
import nav.NavMain
import pandas as pd
import timeit


def main_test_translational():
    # SETUP
    desc = 'main_test - Test NavMain.main translational functionality with high-fidelity inputs'

    # read raw data from input file
    data = pd.read_csv('sim_data.csv')

    # EXPECTED RESULT
    exp = {
        'time': 0.2,
        'position': array([6378137.035530, 0.038250, 0.036250]),
        'velocity': array([0.358000, 0.350000, 0.350000]),
        'attitude': array([1.0, 0.0, 0.0, 0.0])
    }

    # UNIT UNDER TEST
    prev_state = {
        'time': data['t'][0],
        'position': array([data['p_x'][0], data['p_y'][0], data['p_z'][0]]),
        'velocity': array([data['v_x'][0], data['v_y'][0], data['v_z'][0]]),
        'attitude': array([1.0, 0.0, 0.0, 0.0])
    }

    for i in arange(1, len(data['t'])):
        time = data['t'][i]

        p_ecef = array([data['p_x'][i], data['p_y'][i], data['p_z'][i]])
        p_lla = ecef_to_lla(p_ecef)

        accel_nc = array([data['anc_x'][i], data['anc_y'][i], data['anc_z'][i]])

        sensor_data = {
            'time': data['t'][i],
            'altitude': p_lla[2],
            'gps': p_lla,
            'accel_nc': accel_nc,
            'accel_c': accel_nc - G_E*p_ecef/((norm(p_ecef))**3),
            'angular_velocity': array([0.0, 0.0, 0.0]),
            'q_inert_to_body': array([1.0, 0.0, 0.0, 0.0])
        }

        prev_state = nav.NavMain.main(prev_state, sensor_data)

    ret = prev_state

    # RESULTS
    need_to_pass = 4
    need_to_pass -= 1 if ret['time'] == exp['time'] else 0
    need_to_pass -= 1 if allclose(ret['position'], exp['position'], atol=0.001) else 0
    need_to_pass -= 1 if allclose(ret['velocity'], exp['velocity'], atol=0.001) else 0
    need_to_pass -= 1 if allclose(ret['attitude'], exp['attitude'], atol=0.001) else 0

    return (PASS, desc) if need_to_pass == 0 else (FAIL, desc)


def nav_speed_test():
    # SETUP
    max_time = 0.001  # seconds
    desc = 'nav_speed_test - Ensure that NavMain.main runs in less than {} seconds'.format(max_time)

    # read raw data from input file
    data = pd.read_csv('sim_data.csv')

    # UNIT UNDER TEST
    elapsed_times = zeros(len(data['t'])-1)

    prev_state = {
        'time': data['t'][0],
        'position': array([data['p_x'][0], data['p_y'][0], data['p_z'][0]]),
        'velocity': array([data['v_x'][0], data['v_y'][0], data['v_z'][0]]),
        'attitude': array([1.0, 0.0, 0.0, 0.0])
    }

    for i in arange(1, len(data['t'])):
        time = data['t'][i]

        p_ecef = array([data['p_x'][i], data['p_y'][i], data['p_z'][i]])
        p_lla = ecef_to_lla(p_ecef)

        accel_nc = array([data['anc_x'][i], data['anc_y'][i], data['anc_z'][i]])

        sensor_data = {
            'time': data['t'][i],
            'altitude': p_lla[2],
            'gps': p_lla,
            'accel_nc': accel_nc,
            'accel_c': accel_nc - G_E*p_ecef/((norm(p_ecef))**3),
            'angular_velocity': array([0.0, 0.0, 0.0]),
            'q_inert_to_body': array([1.0, 0.0, 0.0, 0.0])
        }

        start_time = timeit.default_timer()
        prev_state = nav.NavMain.main(prev_state, sensor_data)
        elapsed = timeit.default_timer() - start_time
        elapsed_times[i-1] = elapsed

    # RESULTS
    return (PASS, desc) if (elapsed_times < max_time).sum() == len(elapsed_times) else (FAIL, desc)

# Test Loop
def main():
    module_name = 'NavMerge.py'

    tests = [
        main_test_translational,
        nav_speed_test
    ]

    num_tests = len(tests)
    failed = unit_test(module_name, tests)
    return failed, num_tests


if __name__ == '__main__':
    main()
