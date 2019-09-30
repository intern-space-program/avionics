# This script does the following:
#	1) Record H264 Video using PiCam at a maximum bitrate of 300 kbps
#	2) Stream video data to a local BytesIO object
#	3) Send raw data over a upd port to simulate LTE
#	4) Store raw data to an onboard file
#	5) Clears BytesIO object after network stream and file store
#	6) Interrupts and ends recording after 'record_time' seconds

# Author: Ronnie Ankner
# Last Edited: 9/29/19
# Libraries
#	-> picamera -> PiCamera: Enables pi cam interfacing and settings manipulation
#	-> picamera -> PiCameraCircularIO: Allows for a circular buffer (if we want one)
#	-> threading: enables timer interrupt
#	-> io -> BytesIO : local file-like object that camera streams to
#	-> socket: allows for UDP socket and message sending
#============================ To View the UDP stream =======================
# 1) Install Gstreamer
# 2) run the follow command from command line
# 	gst-launch-1.0 -v udpsrc port=4000 ! h264parse ! avdec_h264 ! videoconvert ! autovideosink
#===========================================================================
from picamera import PiCamera
from picamera import PiCameraCircularIO
from io import BytesIO
import threading
import socket
import time

#======================= Global Variables and Objects =================
#Global Variables
record_file = 'buffer_recording.h264' #on-board file video is stored to
bitrate_max = 300000 # bits per second
record_time = 8 # Time in seconds that the recording runs for
record_chunk = 0.2 #chunk size in seconds video object is broken into and sent 
frame_rate = 20 #camera frame rate
interrupt_bool = False #global interrupt flag that ends recording/program
store_and_send_bool = False #global interrupt flag that initiates sending and storing of camera data

#ensures chunk size is not smaller than one frame
if record_chunk < 1/frame_rate:
	record_chunk = 1/frame_rate

#Camera Settings
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = frame_rate

#Network Streaming (REPLACE WITH LTE)
STREAM_IP = '127.0.0.1'
STREAM_PORT = 4000
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


#========================= Functions =================================
def interrupt_func():
	#Interrupt function that ends camera streaming and program
	global interrupt_bool
	interrupt_bool = True
	print("Program Timer up")

def store_interrupt_func():
	#interrupt function that initiates sending and storing camera data
	global store_and_send_bool
	store_and_send_bool = True
	#threading.Timer(record_chunk, store_interrupt_func).start()

def send_network(msg):
	#Sends data over UDP (REPLACE WITH LTE)
	send_sock.sendto(msg, (STREAM_IP, STREAM_PORT))



#======================== Video Streaming and Recording ============
loop_cnt = 0.0
cnt = 0
#camera.start_preview()
"""
#=============================== Stores Directly to file ===============================
# More efficient process, but stores in large chunks (~2s): may be too large for LTE modem to handle

camera.start_recording(record_file, format='h264', bitrate=bitrate_max)
threading.Timer(record_time, interrupt_func).start()
while not(interrupt_bool):
	sleep(0.1)
	loop_cnt+=0.1
	print("Record Time: %f"%(loop_cnt))
#======================================================================================
"""
"""
#=================== Stores to local Circular Buffer then file ========================
#Less efficient (moves data twice), but stores in smaller chunks which may be easier for modem to handle
stream = PiCameraCircularIO(camera, seconds = 10, bitrate=bitrate_max)
camera.start_recording(stream, format='h264', bitrate=bitrate_max)
threading.Timer(record_time, interrupt_func).start()

while not(interrupt_bool):
	camera.wait_recording(record_chunk)
	stream.copy_to(record_file)
	cnt+=1
	print("Saved Chunk #%d"%(cnt))
#======================================================================================
"""

#=================== Stores to local BytesIO then sends========================
#		    MOST EFFICENT AND TEST-PROVEN METHOD

#Initialize local stream object
stream = BytesIO()

#Open and/or create onboard file to store to
camera_file_handle = open(record_file, 'wb+')

#Begin Pi Cam recording
camera.start_recording(stream, format='h264', bitrate=bitrate_max)

#Start timer threads
threading.Timer(record_time, interrupt_func).start()
threading.Timer(record_chunk, store_interrupt_func).start()

time_sum = 0
random_cnt = 0
program_start = time.time()
#Main Program Loop
while not(interrupt_bool):
	#camera.wait_recording(record_chunk)
	if (store_and_send_bool):
		temp_start = time.time()
		#executes when record_chunk thread times out
		#controls how often data is ported ofver the network and to file
		#change 'record_chunk' to vary time and data size
		
		#Reset global interrupt flag
		threading.Timer(record_chunk, store_interrupt_func).start()
		store_and_send_bool = False

		#Send bytes-like date over the Network (UDP)
		send_network(stream.getvalue())
		
		#Store bytes-like data to file 
		camera_file_handle.write(stream.getvalue())
		
		#Clear local file-like object
		stream.truncate(0)
		stream.seek(0)

		#[Optional] Print Diagnostic printout
		#cnt+=1
		#print("Sent and Saved Chunk #%d | Loop Time: %f"%(cnt, (time.time()-temp_start)))
		time_sum+=(time.time() - temp_start)
		
#======================================================================================

#End Recording and Tidy Up
total_time = time.time() - program_start 
print("Ending Recording")
camera.stop_recording()
print("Closing Video File")
camera_file_handle.close()
print("Program Time: %fs"%(total_time))
print("Process Time: %fs"%(time_sum))
print("Program Usage: %f%%"%((time_sum*100)/total_time))


#camera.stop_preview()
