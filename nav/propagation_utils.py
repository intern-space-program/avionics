from numpy import array
from numpy.linalg import norm
from nav.constants import *


def propagate_pv(p_0, v_0, a_1_nc, a_1, dt):
    ''' Propagates the position and velocity of the vehicle.
    
    :param p_0: The last known position of the vehicle.
    :param v_0: The last known velocity of the vehicle.
    :param a_1: The latest mean acceleration measurement.
    :param dt: The time step over which measured acceleration was averaged.

    :type p_0: `numpy.array` [1x3]
    :type v_0: `numpy.array` [1x3]
    :type a_1: `numpy.array` [1x3]
    :type dt: `float`

    :return: tuple of (propagated position p_1, propagated velocity v_1)
    '''

    if norm(p_0) != 0:
        a_1_calculated = a_1_nc + G_E*p_0/p_0**3
    else:
        a_1_calculated = array([0.0, 0.0, 0.0])

    a_1_avg = 0.5*(a_1_calculated+a_1)


    v_1 = v_0 + a_1_avg*dt
    p_1 = p_0 + v_0*dt + 0.5*a_1_avg*dt*dt
    
    return p_1, v_1


def propagate_att(q_inert_to_body_0, q_inert_to_body_new, da_imu, dt):
    ''' Propagates the vehicle's attitude quaternion.

    :param q_inert_to_body_0: the last known attitude quaternion
    :param q_inert_to_body_new: the latest known attitude quaternion
    :param da_imu: the angle-change measurement from the IMU
    :param dt: the delta-time of the IMU measurement

    :type q_inert_to_body_0: `numpy.array` [1x4]
    :type q_inert_to_body_new: `numpy.array` [1x4]
    :type da_imu: `numpy.array` [1x3]
    :type dt: `float`

    :return: `numpy.array` [1x4] the propagated attitude quaternion q_inert_to_body_1
    '''

    pass
