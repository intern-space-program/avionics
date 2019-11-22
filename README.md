# Avionics F2019
## Full System Architecture

![full system](system_diagram.png)

## Payload Architecture

![payload](payload_diagram.jpg)

## Component Descriptions
- **Teensy**: WRITE DESCRIPTION
- **Raspi**: WRITE DESCRIPTION
- **Nav**: The navigation capability keeps us updated on where the vehicle is, its velocity, and its attitude. It incorporates data from all the sensors on board to come up with an estimated state, then does some light filtering to smooth out the data before it gets transmitted to the ground.
- **Ground_station**: WRITE DESCRIPTION
- **Simulation**: WRITE DESCRIPTION
- **Packetizer**: WRITE DESCRIPTION

## Payload Setup and Dependencies
### Set Up Conda Environment
1. Install anaconda: https://www.anaconda.com/distribution/
    - Be sure to download the Python 3 version
2. From the command line, run: `conda create env -f condaenv.yml`
3. Activate the conda environment: `conda activate avionics`

## Ground Station Setup and Dependencies
