# Raspi Folder Description
## Folder Overview
This folder contains all components necessary to create the final flight script for the on-board raspberry pi 0. Folders are broken down by high level component functionality and scripts are broken up into building blocks that accomplish a certain main task on their own: for example, the "Camera" folder contains scripts that were used to refine the functionality of reading and storing video data. 

## Folder Breakdown
 - **Final_Solution**: While poorly named, this is where finished and tested components from other folders go to be refined further and incorporated into the **flight_script.py**, which is the *final implementation that runs on boot and flies on board the payload*.
 - **Camera**: Very first folder that was created and used to find the optimal way to stored video data to a local buffer and access the data to store and send -> customized specifically for the raspberry pi and raspi cam. 
 - **LTE**: Folder used to get accustomed to Hologram Nova python SDK -> methods used here ended up not being the most efficient for our purpose as the built in functions connected with the cell network, then connected with the Hologram server, then sent the message, then disconnected from the Hologram server, and finally ended the cell network connection. This is optimized for small, infrequent packets, *not live streaming video and telemetry*, as the **whole process took roughly 2 seconds** no matter the size of the data packet. Move was made to make connecting to cell tower a standalone process, create out own sever, and have the pi connect to the cell tower and server before the flight, maintain connection throughout, and disconnect from both only after the flight was completed. 
 - **Camera_and_LTE**: initial attempts to link the camera work and LTE SDK, but as mentioned above, was shown to be very inefficient. 
 - **web_sockets**: Folder dedicated to experimenting with different socket techniques and optimize socket operation for live streaming. 

