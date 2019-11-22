# Navigation

## Description
Navigation ("Nav") takes in sensor measurements and the last known state of the rocket and estimates the vehicle's current position, velocity, and attitude. **Units are SI.**

## Use Instructions
In the F2019 semester, the vehicle has the following set of sensors on board, with the specified data used:
- GPS
    - latitude, longitude, altitude (LLA) position (degrees, degrees, meters)
- IMU
    - x, y, z conservative acceleration (includes gravity) (all meters per second squared)
    - x, y, z non-conservative acceleration (gravity subtracted) (all meters per second squared)
    - x, y, z angular velocity (all radians per second)
    - w, x, y, z absolute attitude quaternion (unitless)
- Temperature/Pressure/Altitude
    - z position (meters)
    
This should be compiled into a python dictionary with the following keys and values before being input to Nav:
- `time`: `float` The time at which the sensor measurements were taken
- `altitude`: `float` The GPA sensor's altitude measurement
- `gps`: `numpy.array([1x3])` The GPS sensor's latitude, longitude, altitude position measurement
- `accel_nc`: `numpy.array([1x3])` The IMU's x, y, z non-conservative acceleration measurement
- `accel_c`: `numpy.array([1x3])` The IMU's x, y, z conservative acceleration measurement
- `angular_velocity`: `numpy.array([1x3])` The IMU's x, y, z axis angular velocity measurement
- `q_inert_to_body`: `numpy.array([1x4])` The IMU's orientation quaternion, scalar-first
    
Nav returns a python dictionary with the following keys and values:
- `time`: `float` The time at which the state's values were calculated (s)
- `position`: `numpy.array([1x3])` The x, y, z position (in ECEF frame) (m, m, m)
- `velocity`: `numpy.array([1x3])` The x, y, z velocity (in ECEF frame) (m/s, m/s, m/s)
- `attitude`: `numpy.array([1x4])` A scalar-first right-transform quaternion representing the coordinate transformation from the inertial frame (launchpad frame) to the current frame of the vehicle, effectively representing attitude (unitless)

NavMain.main should be called with the arguments:
- `prev_state`: The last known state of the vehicle (in the form returned by NavMain.main, see above)
- `sensor_data`: The set of recent sensor measurements (in the dictionary form described above)

## Future Work
[See issues with tag "Nav"](https://github.com/intern-space-program/F2019_Avionics/issues?q=is%3Aopen+is%3Aissue+label%3ANAV).

Due to time/human resource constraints in the F2019 semester, the following stretch goals were not met, but could be implemented by future groups if they reuse the Nav code currently developed.

- Some IMUs measure non-conservative acceleration and conservative acceleration separately. Other (cheaper) IMUs just measure conservative acceleration and subtract a gravity term off of it. The IMU used in the F2019 semester is of the latter type, so there is no accuracy to be gained from trying to use both measurements. As such, the Nav code for F2019 only makes use of the non-conservative acceleration measurement. If a different type of IMU is used in the future, `NavMerge.merge_accel` could be updated to make accuracy gains (there is a small bug to be found in the commented-out section of that function).
- If the standard deviations of sensors were known ahead of flight (from testing), these errors could be accounted for in the data merging process. For example, see the commented-out code in `NavMerge.merge_velocity`.
- Adding an airspeed sensor could make the velocity estimate more accurate. See commented-out code in `NavMerge.merge_velocity`.
- There exist several types of quaternions. Two standard types are right-rotation and right-transform quaternions. The `quaternion_utils.py` assumes a scalar-first, right-transform quaternion. However, it was unknown what type of quaternion the IMU returned. This could not be tested ahead of time due to time constraints. Future groups could sync up these quaternion types and reduce error by merging a propagated attitude (using angular velocity measurements) with the absolute attitude measured by the IMU.
- Adding a filtering capability to Nav would make the final data outputs each time Nav is called slightly less noisy. Due to time constraints and the relatively large errors in the sensors used in F2019, this capability was not developed.
