# Avionics
## Purpose of This Repo
Intern Space Program began in 2018, but the Avionics group has struggled consistently due to:
* Poor hardware/software documentation
* Primary goals left incomplete and/or problems unsolved
* Inconsistent handover of work to future tours

This repo is an effort to resolve those issues. Why rebuild from scratch when previous tours have done some of the dirty work? Make use of what's been done and develop new features that you'd like to see. Please see the [CONTRIBUTING guide](https://github.com/intern-space-program/avionics/blob/master/CONTRIBUTING.md) for more information.

## Project Overview and Goals
The intention of this project was to create hardware and software to enable *real-time* streaming of telemetry and video data from within a medium sized rocket. The system was built and developed from the ground up. 
There were two main goals for the system:
1. Live Stream Video and Inertial Data to the World
2. Employ navigation and sensor fusion techniques to localize the payload (and hence rocket) in real time

This project has pushed the bounds in both live streaming video and telemetry data over LTE Cat M-1 and functionality given the limited amount of space in the nosecone. The hope is that future teams will be able to build off of this platform and further the success of the intern space program as a whole.

## Setup
1. Install python.
2. From your command line, run `pip install -r requirements.txt` from the repo's directory.

## System Diagrams
### Full System Architecture

![full system](img/system_diagram.png)

### Payload Architecture

![payload](img/payload_diagram.jpg)

### Server Architecture

![payload](img/server_diagram.jpg)

## Component Descriptions
- **Teensy**:The Teensy folder contains the Arduino file that allows the co-processor to go through the initiation and calibration procedure and to  sample data from the sensor suite, serializing this data via a JSON packet to be sent to the Pi for distribution.
- **Raspi**: The raspi folder is dedicated to developing the tools necessary to operate the on-board raspberry pi zero, which is responsible for: 
  1. reading/compressing video data
  2. reading in raw telemetry from the teensy
  3. storing video and telemetry data
  4. sending video and telemetry data over the LTE network to the ground server
- **Nav**: The navigation capability keeps us updated on where the vehicle is, its velocity, and its attitude. It incorporates data from all the sensors on board to come up with an estimated state, then does some light filtering to smooth out the data before it gets transmitted to the ground.
- **Ground_station**: The ground_station folder contains scripts to operate the ground server and client, and also scripts to create and display the telemetry display GUI
- **Simulation**: the simulation folder contains scripts to generate random, but realistic trajectories and generate varying degress of sensor data from the trajectories to test and flesh out the navigation algorithms. 
- **Packetizer**: the packetizer folder contains a C-style implementation of payloading and de-payloading the raw telemetry data in a highly efficient structure and byte format. 

## Hardware List Fall 2019
- [Raspberry Pi 3 Model B](https://www.adafruit.com/product/3775?src=raspberrypi)
- [Raspberry Pi Zero](https://www.adafruit.com/product/3708)
- [Raspberry Pi Camera](https://www.amazon.com/Raspberry-Pi-Camera-Module-Megapixel/dp/B01ER2SKFS)
- [Adafruit GPS Sensor](https://www.adafruit.com/product/746)
- [Adafruit Temp/Press Altitude Sensor](https://www.adafruit.com/product/2651)
- [Adafruit IMU](https://learn.adafruit.com/adafruit-bno055-absolute-orientation-sensor/overview)

## Payload Setup and Dependencies
### Install Hologram Nova API
## Ground Station Setup and Dependencies
### Video Streaming and Display
### GUI Display
### Screen Streaming to the World
