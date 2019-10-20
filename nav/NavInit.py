from numpy import array
from numpy.linalg import norm


class NavInit:
    def __init__(self):
        self.w_alt = 1.0  # weight of altimeter measurements
        self.w_gps = 1.0  # weight of gps measurements

        # initialization values
        self.t_state = 0.0  # time of last known state

        # position vectors
        self.r_body_in_inert = array([0.0, 0.0, 1e-6])
        self.r_earth_in_imu = array([0.0, 0.0, -1.0])
        self.r_magf_in_imu = array([1.0, 0.0, 0.0])

        # rate vectors
        self.v_body_in_inert = array([0.0, 0.0, 0.0])
        self.airspeed = norm(self.v_body_in_inert)
        self.a_imu_nc_wrt_inert_in_imu = array([0.0, 0.0, 0.0])
        self.a_imu_wrt_inert_in_imu = array([0.0, 0.0, 0.0])
        self.w_imu_wrt_inert_in_imu = array([0.0, 0.0, 0.0])

        # quaternions
        self.q_body_to_imu = array([0.0, 0.0, 0.0, 1.0])
        self.q_inert_to_body = array([0.0, 0.0, 0.0, 1.0])
        self.q_inert_to_imu = array([0.0, 0.0, 0.0, 1.0])
