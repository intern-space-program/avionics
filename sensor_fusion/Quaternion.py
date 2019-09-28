'''
File name: Quaternion.py
Created by: Mike Bernard
Creator email: mike.bernard@uconn.edu
Creation date: 2019-09-28

Python version: 3.7.3

A quaternion class that handles basic operations of
unit transform right quaternions.
'''

from numpy import array
from numpy.linalg import norm
from .Vector import Vector


class Quaternion:
    def __init__(self, vec, s, smallangle=False):
        '''
        :param vec: The vector part of the quaternion
        :type vec: `Vector` object
        :param s: The scalar part of the quaternion
        :type s: `float`
        '''

        self.v = vec  # `Vector` vector part
        self.s = s    # `float` scalar part

    def conjugate(self):
        '''
        Get the conjugate of a quaternion. This is equal to
        the inverse for unit quaternions.
        '''
        return Quaternion(-1*self.v, self.s)

    def vectransform(self, vec):
        '''
        Transform a vector's frame.
        '''
        qvec = Quaternion(vec, 0)  # pure quaternion
        transformed = self.qcomp(self, self.qcomp(qvec, self.conjugate()))
        return transformed.v

    @staticmethod
    def qcomp(q1, q2):
        '''
        Compose two quaternions using Malcolm Shuster's convention.
        '''

        v = q1.s*q2.v + q2.s*q1.v - Vector.vcross(q1.v, q2.v)
        s = q1.s*q2.s - Vector.vdot(q2.v, q1.v)

        return Quaternion(v, s)

    @staticmethod
    def qnormalize(q):
        '''
        Normalize a quaternion.
        '''

        qn = array([q.v.v[0], q.v.v[1], q.v.v[2], q.s])
        qn = qn/norm(qn)
        return qn
