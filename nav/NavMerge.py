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
                 delta_theta=None, accel_nc=None, accel=None, sigmas=None):
        '''
        :param prev_state: Last known state vector
        :param dt: Delta time between last known state and current measurements
        :param airspeed: Magnitude of velocity vector
        :param altitude: Height (z) above ground
        :param gps: Postion vector (x, y, z) measured by the GPS
        :param delta_theta: Delta-angle vector (da_x, da_y, da_z) measured by IMU
        :param accel_nc: Non-conservative (no gravity) acceleration vector (d2x, d2y, d2z) measured by IMU
        :param accel: Conservative acceleration vector (d2x, d2y, d2z) measured by IMU
        :param sigmas: The standard deviations of the sensors

        :type prev_state: `dict` of `string`: `np.array([])` and `string`: `float`
        :type dt: `float`
        :type airspeed: `float`
        :type altitude: `float`
        :type gps: `np.array([])` [1x3]
        :type delta_theta: `np.array([])` [1x3]
        :type accel_nc: `np.array([])` [1x3]
        :type accel: `np.array([])` [1x3]
        :type sigmas: `dict`

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
        self.sigmas = sigmas

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
        Integrate IMU linear acceleration into linear velocity.

        :return: `numpy.array` of new velocity
        '''
        v_prev = self.prev_state['velocity']
        v_new = v_prev + self.accel_merged*self.dt

        return v_new

    def merge_airspeed_and_zdot(self):
        pass

    def merge_position_terms(self):
        pass

    @staticmethod
    def weighted_avg(values, weights):
        '''
        Takes a list of values and a list of weights associated
        with those values (index-to-index) and returns a weighted
        averaged of those values as a float.
        '''
        denom = sum([1/w**2 for w in weights])
        num = sum([1/w**2 * v for v, w in zip(values, weights)])

        return num/denom

    def merge_velocity_terms(self):
        v_new_i = self.integrate_imu_linear()
        std_imu = self.sigmas['IMU']
        std_airspeed = self.sigmas['airspeed']
        v_new_mag = norm(v_new_i)
        v_new_mag_est = self.weighted_avg([v_new_mag, self.airspeed],
                                          [std_imu, std_airspeed])

        return v_new_mag_est * v_new_i / v_new_mag

    def merge_attitude_quaternions(self):
        pass

    def get_merged_state(self):
        pass
