'''
File name: frame_utils.py
Programmed by: Mike Bernard
Date: 2019-11-16

Functions to convert between several different types of frames.
'''

from numpy import array, cos, sin, tan, arctan, deg2rad, sqrt, arctan2, rad2deg, pi
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

    # calculate ECEF position
    x = r_s*cos(lambda_s)*cos(long) + alt*cos(lat)*cos(long)
    y = r_s*cos(lambda_s)*sin(long) + alt*cos(lat)*sin(long)
    z = r_s*sin(lambda_s) + alt*sin(lat)

    return array([x, y, z])


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

    # calculate longitude
    long = arctan2(y, x)

    # calculate latitude using iterative Bowring's method
    s = sqrt(x**2 + y**2)
    Beta = arctan2(z, ((1-flattening)*s))
    e_squared = 1 - (1-flattening)**2
    lat_num = z + e_squared*(1-flattening)/(1-e_squared)*radius_equatorial*(sin(Beta))**3
    lat_den = s - e_squared*radius_equatorial*(cos(Beta))**3
    lat = arctan2(lat_num, lat_den)
    converged = True if abs(lat) == pi else False
    while not converged:
        Beta = arctan(((1-flattening)*sin(lat))/cos(lat))
        lat_num = z + e_squared*(1-flattening)/(1-e_squared)*radius_equatorial*(sin(Beta))**3
        lat_den = s - e_squared*radius_equatorial*(cos(Beta))**3
        if round(arctan2(lat_num, lat_den), 4) == round(lat, 4):  # arbitrary 4 decimals of precision
            lat = arctan2(lat_num, lat_den)
            converged = True
        else:
            lat = arctan2(lat_num, lat_den)

    # calculate altitude
    N = radius_equatorial / sqrt(1 - e_squared*(sin(lat))**2)
    alt = s*cos(lat) + (z + e_squared*N*sin(lat))*sin(lat) - N

    # convert lat, long from radians to degrees
    lat = rad2deg(lat)
    long = rad2deg(long)

    return array([lat, long, alt])
