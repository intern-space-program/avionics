from numpy import array, concatenate
from numpy.linalg import norm


class VehicleState:
    def __init__(self, q_body_to_imu):
        '''
        The vehicle's state, incorporating:
            - position
            - linear velocity
            - attitude

        Default values are overwritten at startup.

        :param q_body_to_imu: The relative orientation of the IMU frame to
            the vehicle body frame.
        :type q_body_to_imu: `numpy.array`
        '''

        # scalars
        self.t_state = 0.0  # time of last known state
        self.airspeed = norm(self.v_body_in_inert)

        # position vectors
        self.r_body_in_inert = array([0.0, 0.0, 1e-6])
        self.r_earth_in_imu = array([0.0, 0.0, -1.0])
        self.r_magf_in_imu = array([1.0, 0.0, 0.0])

        # rate vectors
        self.v_body_in_inert = array([0.0, 0.0, 0.0])
        self.a_imu_nc_wrt_inert_in_imu = array([0.0, 0.0, 0.0])
        self.a_imu_wrt_inert_in_imu = array([0.0, 0.0, 0.0])
        self.w_imu_wrt_inert_in_imu = array([0.0, 0.0, 0.0])

        # quaternions
        self.q_body_to_imu = q_body_to_imu
        self.q_inert_to_body = array([0.0, 0.0, 0.0, 1.0])
        self.q_inert_to_imu = array([0.0, 0.0, 0.0, 1.0])

        ''' State Vector, `list`, all components resolved in inertial frame
            [0:3]  : vehicle position vector
            [4:6]  : vehicle velocity vector
            [7:10] : vehicle attitude quaternion '''
        self.state_vector = concatenate([self.r_body_in_inert,
                                         self.v_body_in_inert,
                                         self.q_inert_to_body])

    def get_update(self):
        '''
        Updates the vehicle's state based on the current measurements.
        :return: self.state_vector
        '''

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
        :return: returns return of self.get_update()
        '''
        self.t_state = measurements[0]  # time of measurements
        imu = measurements[1]  # imu measurements
        gps = measurements[2]  # gps measurements
        airspeed = measurements[3]  # pitot tube reading converted to airspeed
        tp = measurements[4]  # temp./press. readings

        self.parse_imu(imu)
        self.parse_gps(gps)
        self.airspeed = airspeed
        self.parse_tp(tp)

        return self.get_update()

    def parse_imu(self, imu):
        '''
        Parses out the data measured by the IMU.
        :param imu: values measured by the IMU.
        :type imu: `list`
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
