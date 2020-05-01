# Avionics

## What's This?
Avionics is the neural system of the vehicle. On a real rocket, the avionics control the vehicle during flight, and handle all communication with the ground systems. In the Intern Space Program, the avionics software does things like estimate the vehicle's position throughout the flight, stream a live video feed from the rocket, and controls the detonation charge for the parachutes.

## How to Contribute to Avionics
Current projects can be found under the Projects tab. In each project, you can find descriptive notes and related issues. All issues can be found in the Issues tab. You should look for ones tagged "Good First Issue" if you're new to programming/git, or ones related to your team's capability. When you think you've solved an issue or a few related ones, make a Pull Request and ask the avionics leads for a review. They'll give you changes to make or merge your Pull Request into the master branch.

If you're new to git, and you're having trouble figuring out how to get started, feel free to ask the avionics lead for instructions.

## Design Philosophy
As with all projects, avionics began with a pile of rag-tag code that barely functioned. That kind of code is really difficult for new people to understand and use, and even more difficult to build on.

The design philosophy is simple: keep things bite-sized. Try to avoid thousand-line scripts. Keep things modular, split across functions and scripts, and well-documented.

## Development Process
  1. Generally describe a new thing you want avionics to do.
  2. Specifically describe what **kind** of data (not specific datatype) you want the new system to receive, and what it'll output.
  3. Look at the existing modules. What kind of data do they output? Can you design your system to use the existing datatypes they output? If so, do so.
  4. Try to design your system so that it can be used in just a few lines of code in the master script. (I.e. we don't want to call every function in your system in the master script. Have a main function in your system that does all that, and we'll call just that function from the master script.)
  5. Work with the avionics lead to decide how the main avionics control script will call on your system.
  6. Create issues for your system on git. Make as many as you want. Tag them appropriately, and assign yourself to them.
  7. Write integration tests first. Yes, that's right: don't write the system code yet. If you can write tests for your system, then you definitely know what you want it to get and give back.
  8. Program your system. Try to chunk it up into as many small functions as possible, maybe across multiple scripts if necessary. The goal is to make the code as readable as possible in bite-sized chunks. For every function you write, write a unit test or two so you can validate that it works correctly and won't crash (e.g. does it have a division-by-zero checker?).
  9. Create a Pull Request for your system and request that the avionics lead review it.

## Capabilities
- **Sensor Suite**: Parse data produced by sensors.
- **Camera**: Record live video of the flight.
- **Navigation**: Estimate the vehicle's current position, velocity, and attitude.
- **Telemetry Streaming**: Communication between the vehicle and the ground station.
- **Ground Station**: Display the flight telemetry and video feed in a nice-looking way.

See each capability's README file for more specific information.

## Hardware List Fall 2019
- [Raspberry Pi 3 Model B](https://www.adafruit.com/product/3775?src=raspberrypi)
- [Raspberry Pi Zero](https://www.adafruit.com/product/3708)
- [Raspberry Pi Camera](https://www.amazon.com/Raspberry-Pi-Camera-Module-Megapixel/dp/B01ER2SKFS)
- [Adafruit GPS Sensor](https://www.adafruit.com/product/746)
- [Adafruit Temp/Press Altitude Sensor](https://www.adafruit.com/product/2651)
- [Adafruit IMU](https://learn.adafruit.com/adafruit-bno055-absolute-orientation-sensor/overview)
