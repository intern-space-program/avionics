'''
File name: frame_utils.py
Programmed by: Mike Bernard
Date: 2019-11-16

Functions to convert between several different types of frames.
'''

from numpy import array, cos, sin, tan, arctan, deg2rad, sqrt
from nav.utils.constants import flattening, radius_equatorial


def lla_to_ecef(lla_array):
    '''
    Convert from GPS (latitude, longitude, altitude) to
    Earth-centered, Earth-fixed (x, y, z) position.

    Reference:
    https://www.mathworks.com/help/aeroblks/llatoecefposition.html

    :param lla_array: `numpy.array([1x3])` array of (lat, long, alt) [deg, deg, m] as `float`
    :return: `numpy.array([1x3])` ECEF (x, y, z) [m] position
    '''
    # unpack lla_array
    lat, long, alt = lla_array

    # convert lat/long from degrees to radians
    lat = deg2rad(lat)
    long = deg2rad(long)

    # calculate geocentric latitude at mean sea-level
    lambda_s = arctan((1-flattening)**2 * tan(lat))

    # calculate radius at a surface point
    r_s = sqrt(radius_equatorial**2 / \
               (1 + (1/((1-flattening)**2) - 1)*(sin(lambda_s))**2))

    return array([
        r_s*cos(lambda_s)*cos(long) + alt*cos(lat)*cos(long),
        r_s*cos(lambda_s)*sin(long) + alt*cos(lat)*sin(long),
        r_s*sin(lambda_s) + alt*sin(lat)
    ])


def ecef_to_lla(ecef_array):
    '''
    Convert from (x, y, z) [m] position in Earth-Centered, Earth-Fixed
    frame to (latitude, longitude, altitude) [deg, deg, m] array in LLA.

    Reference:
    https://www.mathworks.com/help/aeroblks/ecefpositiontolla.html

    :param ecef_array: `numpy.array([1x3])` array of (x, y, z) [m] as `float`
    :return: `numpy.array([1x3])` LLA (lat, long, alt) [deg, deg, m] position
    '''
    # unpack ecef array
    x, y, z = ecef_array
    long = arctan(ecef[1)