# Navigation

## Description
Navigation ("Nav") takes in sensor measurements and the last known state of the rocket and estimates the vehicle's current position, velocity, and attitude.

## Use Instructions
In the F2019 semester, the vehicle has the following set of sensors on board, with the specified data used:
- GPS
    - x, y, z position
- IMU
    - x, y, z conservative acceleration (includes gravity)
    - x, y, z non-conservative acceleration (gravity subtracted)
    - x, y, z angular velocity
- Temperature/Pressure/Altitude
    - z position
    
This should be compiled into a python dictionary with the following keys and values before being input to Nav:
- `time`: `float` The time at which the sensor measurements were taken
- `altitude`: `float` The GPA sensor's altitude measurement
- `gps`: `numpy.array([1x3])` The GPS sensor's x, y, z position measurement
- `accel_nc`: `numpy.array([1x3])` The IMU's x, y, z non-conservative acceleration measurement
- `accel_c`: `numpy.array([1x3])` The IMU's x, y, z conservative acceleration measurement
- `angular_velocity`: `numpy.array([1x3])` The IMU's x, y, z axis angular velocity measurement
- `q_inert_to_body`: `numpy.array([1x4])` The IMU's orientation quaternion, scalar-first
    
Nav returns a python dictionary with the following keys and values:
- `time`: `float` The time at which the state's values were calculated
- `position`: `numpy.array([1x3])` The x, y, z position
- `velocity`: `numpy.array([1x3])` The x, y, z velocity
- `attitude`: `numpy.array([1x4])` A scalar-first right-transform quaternion representing the coordinate transformation from the inertial frame (launchpad frame) to the current frame of the vehicle, effectively representing attitude

NavMain.main should be called with the arguments:
- `prev_state`: The last known state of the vehicle (in the form returned by NavMain.main, see above)
- `sensor_data`: The set of recent sensor measurements (in the dictionary form described above)
