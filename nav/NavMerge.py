'''
NavMerge takes in sensor data that has been formatted by
NavReceive and outputs data that has been merged to a
minimized state vector.
'''

import numpy as np
from nav.quaternion_utils import *
from nav.constants import *


class NavMerge:
    def __init__(self, prev_state, dt=0, airspeed=None, altitude=None, gps=None,
                 delta_theta=None, accel_nc=None, accel=None):
        '''
        :param prev_state: Last known state vector
        :param dt: Delta time between last known state and current measurements
        :param airspeed: Magnitude of velocity vector
        :param altitude: Height (z) above ground
        :param gps: Postion vector (x, y, z) measured by the GPS
        :param delta_theta: Delta-angle vector (da_x, da_y, da_z) measured by IMU
        :param accel_nc: Non-conservative (no gravity) acceleration vector (d2x, d2y, d2z) measured by IMU
        :param accel: Conservative acceleration vector (d2x, d2y, d2z) measured by IMU

        :type prev_state: `dict` of `string`: `np.array([])` and `string`: `float`
        :type dt: `float`
        :type airspeed: `float`
        :type altitude: `float`
        :type gps: `np.array([])` [1x3]
        :type delta_theta: `np.array([])` [1x3]
        :type accel_nc: `np.array([])` [1x3]
        :type accel: `np.array([])` [1x3]

        :return: `np.array([])`
        '''
        self.prev_state = prev_state
        self.dt = dt
        self.airspeed = airspeed
        self.altitude = altitude
        self.gps = gps
        self.delta_theta = delta_theta
        self.accel_nc = accel_nc
        self.accel = accel

        self.accel_merged = self.merged_accel()

    def merge_z_terms(self):
        pass

    def merged_accel(self):
        p_prev = self.prev_state['position']

        if norm(p_prev) != 0:
            a_1_calulated = self.accel_nc + G_E*p_prev/p_prev**3
            a_1_avg = 0.5*(a_1_calulated + self.accel)
        else:
            a_1_avg = self.accel

        return a_1_avg

    def integrate_imu_linear(self):
        '''
        Integrate IMU linear acceleration into linear
        velocity and position.

        :return: `tuple` of (`numpy.array`, `numpy.array` of
                 integrated position and velocity vectors.
        '''
        v_prev = self.prev_state['velocity']
        p_prev = self.prev_state['position']

        v_new = v_prev + self.accel_merged*self.dt
        p_new = p_prev + v_prev*self.dt + 0.5*self.accel_merged*self.dt**2

        return p_new, v_new


    def merge_airspeed_and_zdot(self):
        pass

    def merge_position_terms(self):
        pass

    def merge_velocity_terms(self):
        pass

    def merge_attitude_quaternions(self):
        pass

    def get_merged_state(self):
        pass
