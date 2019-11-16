from numpy import array, cos, sin, tan, arctan, deg2rad, sqrt
from nav.utils.constants import *


def lla_to_ecef(lla_array):
    '''
    Convert from GPS (latitude, longitude, altitude) to
    Earth-centered, Earth-fixed (x, y, z) position.
    :param lla_array: `numpy.array([1x3])` array of (lat, long, alt) as `float`
    :return: `numpy.array([1x3])` ECEF (x, y, z) position
    '''
    # unpack lla_array
    lat = lla_array[0]
    long = lla_array[1]
    alt = lla_array[2]

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
