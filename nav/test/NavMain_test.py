'''
File name: NavMain_test.py
Programmed by: Mike Bernard
Date: 2019-11-05

This is a unit test of the nav_main function.
This also serves as an effective integration test for
the Nav design for F2019.
'''

from numpy import array, allclose
from numpy.linalg import norm
from nav.utils.common_utils import unit_test
from nav.utils.constants import PASS, FAIL, G_E
import nav.NavMain


def main_test():
    # SETUP
    desc = 'main_test_null - Test NavMain.main with high-fidelity inputs'
    # read raw data from input file
    data = []
    with open('avp_sim_data.csv', 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.replace('\n', '').split(',')
            t = float(line[0])
            ax, ay, az = float(line[1]), float(line[2]), float(line[3])
            vx, vy, vz = float(line[4]), float(line[5]), float(line[6])
            px, py, pz = float(line[7]), float(line[8]), float(line[9])
            data.append({
                't': t,
                'a': array([ax, ay, az]),
                'v': array([vx, vy, vz]),
                'p': array([px, py, pz])
            })

    # create initial state for propagation
    init_state = {
        'time': 0.0,
        'position': array([0.0, 0.0, 0.0]),
        'velocity': array([0.0, 0.0, 0.0]),
        'attitude': array([1.0, 0.0, 0.0, 0.0])
    }

    # convert raw input data to format expected by nav
    sensor_outputs = []
    for datum in data:
        time = datum['t']
        altitude = datum['p'][2]
        gps = datum['p']
        accel_nc = datum['a']

        if abs(norm(gps)) >= 0.00000001:
            accel_c = datum['a'] + G_E*gps/((norm(gps))**3)
        else:
            accel_c = array([0.0, 0.0, 0.0])

        q_inert_to_body = array([1.0, 0.0, 0.0, 0.0])
        angular_velocity = array([0.0, 0.0, 0.0])
        sensor_outputs.append({
            'time': time,
            'altitude': altitude,
            'gps': gps,
            'accel_nc': accel_nc,
            'accel_c': accel_c,
            'angular_velocity': angular_velocity,
            'q_inert_to_body': q_inert_to_body
        })

    # EXPECTED RESULTS
    exp = {
        'time': 0.4,
        'position': array([0.002, 0.002, 0.002]),
        'velocity': array([0.0, 0.0, 0.0]),
        'attitude': array([1.0, 0.0, 0.0, 0.0])
    }

    # TEST
    ret = init_state
    for sensor_output in sensor_outputs:
        ret = nav.NavMain.main(ret, sensor_output)

    # RESULTS
    need_to_pass = 4
    need_to_pass -= 1 if ret['time'] == exp['time'] else 0
    need_to_pass -= 1 if allclose(ret['position'], exp['position'], atol=0.00001) else 0
    need_to_pass -= 1 if allclose(ret['velocity'], exp['velocity'], atol=0.00001) else 0
    need_to_pass -= 1 if allclose(ret['attitude'], exp['attitude'], atol=0.00001) else 0

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
