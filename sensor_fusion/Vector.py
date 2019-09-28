'''
File name: Vector.py
Created by: Mike Bernard
Creator email: mike.bernard@uconn.edu
Creation date: 2019-09-28

A vector class that handles basic operations of
vectors in R^3.
'''

from numpy import array, dot, cross


class Vector:
    def __init__(self, x, y, z):
        self.v = array([x, y, z])

    @staticmethod
    def vdot(v1, v2):
        return dot(v1.v, v2.v)

    @staticmethod
    def vcross(v1, v2):
        return cross(v1.v, v2.v)
