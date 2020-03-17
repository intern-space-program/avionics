'''
File name: quaternion_utils.py
Programmed by: Mike Bernard
Date: 2019-09-28

Tools for dealing with scalar-first, rotational, unit,
right quaternions with Hamilton's conventions.

Useful paper on understanding quaternions:
https://www.researchgate.net/publication/330565176_Rotations_Transformations_Left_Quaternions_Right_Quaternions

Conventions used are identical to those used by the
Adafruit BNO055 IMU. These conventions can be seen here:
https://github.com/adafruit/Adafruit_BNO055/blob/master/utility/quaternion.h
'''

from numpy import array, zeros, cross, dot, concatenate, sin, cos
from numpy.linalg import norm


def qcomp(q1, q2):
    ''' Compose two quaternions. '''
    q = zeros(4)
    q[0] = q1[0]*q2[0] - dot(q2[1:], q1[1:])
    q[1:] = q1[0]*q2[1:] + q2[0]*q1[1:] + cross(q1[1:], q2[1:])
    return q


def qnorm(q):
    ''' Normalize a quaternion. '''
    if norm(q) != 0.0:
        return q/norm(q)
    return zeros(4)


def qvectransform(q, v):
    '''
    Transform a vector's frame.
    This is distinct from rotating a vector within a frame!
    See the paper by Robert Zanetti cited in the docstring.
    '''
    qvec = concatenate([array([0]), v])
    transformed = qcomp(qconjugate(q), qcomp(qvec, q))
    return transformed[1:]


def qconjugate(q):
    ''' Get the conjugate of a quaternion. This is equal to
    the inverse for unit quaternions. '''
    qconj = concatenate([array([q[0]]), -q[1:]])
    return qconj
