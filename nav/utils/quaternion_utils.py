'''
File name: quaternion_utils.py
Created by: Mike Bernard
Creator email: mike.bernard@uconn.edu
Creation date: 2019-09-28

Python version: 3.7.3

Tools for dealing with scalar-first, transform, unit,
right quaternions with Malcolm Shuster's conventions.
'''

from numpy import array, cross, dot, concatenate, sin, cos
from numpy.linalg import norm


def qcomp(q1, q2):
    '''
    Compose two quaternions.
    '''
    q1s = q1[0]
    q1v = array(q1[1:])
    q2s = q2[0]
    q2v = array(q2[1:])

    s = array([q1s * q2s - dot(q2v, q1v)])
    v = q1s*q2v + q2s*q1v - cross(q1v, q2v)

    return concatenate([s, v])


def qnorm(q):
    '''
    Normalize a quaternion.
    '''
    if norm(q) != 0.0:
        return q/norm(q)
    else:
        return array([0.0, 0.0, 0.0, 0.0])


def qvectransform(q, v):
    '''
    Transform a vector's frame.
    '''
    qvec = concatenate([array([0]), v])
    transformed = qcomp(q, qcomp(qvec, qconjugate(q)))
    return transformed[1:]


def qconjugate(q):
    '''
    Get the conjugate of a quaternion. This is equal to
    the inverse for unit quaternions.
    '''
    return concatenate([array([q[0]]), -1*q[1:]])


def axis_angle_to_quaternion(axis, angle_rad):
    '''
    Convert an Euler axis and angle to a quaternion.
    :param axis: `np.array([1x3])` (--) The axis of rotation
    :param angle_rad: `float` (rad) The angle of rotation
    :return: `np.array([1x4])` (--) Quaternion representing transformation
    '''
    s = array([cos(angle_rad/2.0)])
    v = sin(angle_rad/2.0) * axis
    return concatenate([s, v])
