from numpy import array
from numpy.linalg import norm


class VehicleState:
    def __init__(self, q_body_to_imu):
        '''
        The vehicle's state, incorporating:
            - position
            - linear velocity
            - attitude

        :param q_body_to_imu: The relative orientation of the IMU frame to
            the vehicle body frame.
        :type q_body_to_imu: `numpy.array`
        '''

        self.q_body_to_imu = q_body_to_imu

        # defaults to be overwritten on startup

        # scalars
        self.t_state = 0.0  # time of last known state
        self.airspeed = norm(self.v_body_in_inert)

        # position vectors
        self.r_body_in_inert = array([0.0, 0.0, 1e-6])

        # rate vectors
        self.v_body_in_inert = array([0.0, 0.0, 0.0])

        # quaternions
        self.q_inert_to_body = array([0.0, 0.0, 0.0, 1.0])
        self.q_inert_to_imu = array([0.0, 0.0, 0.0, 1.0])
        self.w_imu_wrt_inert_in_imu = array([0.0, 0.0, 0.0])
        self.a_imu_nc_wrt_inert_in_imu = array([0.0, 0.0, 0.0])
        self.a_imu_wrt_inert_in_imu = array([0.0, 0.0, 0.0])
        self.r_earth_in_imu = array([0.0, 0.0, -1.0])
        self.r_magf_in_imu = array([1.0, 0.0, 0.0])

    def get_update(self):
        pass

    def set_measurements(self, measurements):
        '''
        Set all the new measurement values needed to propagate the state.
        :param measurements: The latest measurement values recorded.
        :type measurements: `list` of:
            0: `float`
            1: `list`
            2: `list`
            3: `float`
            4: `list`
        '''
        self.t_state = measurements[0]  # time of measurements
        imu = measurements[1]           # imu measurements
        gps = measurements[2]           # gps measurements
        airspeed = measurements[3]      # pitot tube reading converted to airspeed
        tp = measurements[4]            # temp./press. readings

        self.parse_imu(imu)
        self.parse_gps(gps)
        self.airspeed = airspeed
        self.parse_tp(tp)

    def parse_imu(self, imu):
        '''
        Parses out the data measured by the IMU.
        :param imu: List of values measured by the IMU.
        '''

        # imu attitude (scalar-last, unit, transform, right quaternion)
        self.q_inert_to_imu = array([imu[0], imu[1], imu[2], imu[3]])

        # angular velocity of imu wrt inertial frame, components in IMU frame
        self.w_imu_wrt_inert_in_imu = array([imu[4], imu[5], imu[6]])

        # non-conservative acceleration of IMU wrt inertial frame
        # components in IMU frame
        self.a_imu_nc_wrt_inert_in_imu = array([imu[7], imu[8], imu[9]])

        # total acceleration of IMU wrt inertial frame, components in IMU frame
        self.a_imu_wrt_inert_in_imu = array([imu[10], imu[11], imu[12]])

        # position of Earth CG, components in IMU frame
        self.r_earth_in_imu = array([imu[13], imu[14], imu[15]])

        # direction of local magnetic field, components in IMU frame
        self.r_magf_in_imu = array([imu[16], imu[17], imu[18]])

    def parse_gps(self, gps):
        pass

    def parse_tp(self, tp):
        pass
