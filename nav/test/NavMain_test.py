'''
File name: NavMain_test.py
Programmed by: Mike Bernard
Date: 2019-11-05

This is a unit test of the nav_main function.
This also serves as an effective integration test for
the Nav design for F2019.
'''

from numpy import array, allclose, arange
from numpy.linalg import norm
from nav.utils.frame_utils import lla_to_ecef, ecef_to_lla
from nav.utils.common_utils import unit_test
from nav.utils.constants import PASS, FAIL, G_E
import nav.NavMain
import pandas as pd


def main_test():
    # SETUP
    desc = 'main_test - Test NavMain.main with high-fidelity inputs'

    # read raw data from input file
    data = pd.read_csv('sim_data.csv')
    state_init = {
        't': data['t'][0],
        'p_ecef': array([data['p_x'][0], data['p_y'][0], data['p_z'][0]]),
        'v': array([data['v_x'][0], data['v_y'][0], data['v_z'][0]]),
        'a': array([data['anc_x'][0], data['anc_y'][0], data['anc_z'][0]]),
    }

    # EXPECTED RESULT
    exp = {
        'time': 0.2,
        'position': array([6378137.035530, 0.038250, 0.036250]),
        'velocity': array([0.358000, 0.350000, 0.350000]),
        'attitude': array([1.0, 0.0, 0.0, 0.0])
    }

    # UNIT UNDER TEST
    prev_state = {
        'time': state_init['t'],
        'position': state_init['p_ecef'],
        'velocity': state_init['v'],
        'attitude': array([1.0, 0.0, 0.0, 0.0])
    }

    for i in arange(1, len(data['t'])):
        time = data['t'][i]

        p_ecef = array([data['p_x'][i], data['p_y'][i], data['p_z'][i]])
        p_lla = ecef_to_lla(p_ecef)
        altitude = p_lla[2]
        gps = p_lla

        accel_nc = array([data['anc_x'][i], data['anc_y'][i], data['anc_z'][i]])
        accel_c = accel_nc - G_E*p_ecef/((norm(p_ecef))**3)

        angular_velocity = array([0.0, 0.0, 0.0])
        q_inert_to_body = array([1.0, 0.0, 0.0, 0.0])

        sensor_data = {
            'time': data['t'][i],
            'altitude': altitude,
            'gps': gps,
            'accel_nc': accel_nc,
            'accel_c': accel_c,
            'angular_velocity': angular_velocity,
            'q_inert_to_body': q_inert_to_body
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


# Test Loop
def main():
    module_name = 'NavMerge.py'

    tests = [
        main_test
    ]

    unit_test(module_name, tests)


if __name__ == '__main__':
    main()
