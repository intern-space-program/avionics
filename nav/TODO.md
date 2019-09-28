# TODO and Misc. Notes

## TODO
- [X] Create Quaternion tools
- [X] Create Vector tools
- [ ] Convert Quaternion/Vector tools to C for faster computation

## Sensor Data

- IMU:
    - Absolute attitude (quaternion, 100 Hz)
    - Angular velocity (vector, 3-axis, 100 Hz)
    - Acceleration total (vector, 3-axis, 100 Hz)
        - Includes gravity component
    - Acceleration non-conservative (vector, 3-axis, 100 Hz)
        - Does not include gravity component
    - Magnetic field strength (vector, 3-axis, 20 Hz)
    - Gravity (vector, 3-axis, 100 Hz)
   
