'''
File name: constants.py
Programmed by: Mike Bernard
Date: 2019-11-16

Provides constants used throughout multiple scripts.
'''

# Physical Constants
G = 6.67408e-11  # (m**3/kg/s**2) gravitational constant

# Earth Constants
M_E = 5.972e24   # (kg) mass of Earth
G_E = G*M_E      # (m**3/s**2) gravitational parameter of Earth
ACC_GRAV = 9.81  # (m/s**2) gravitational acceleration near Earth's surface

flattening_reciprocal = 298.257223563   # (--) WGS 84 Earth Reciprocal of Flattening
flattening = 1 / flattening_reciprocal  # (--) WGS 84 Earth Flattening Parameter
radius_equatorial = 6378137  # (m) equatorial radius

# Conventions
PASS = 0
FAIL = 1