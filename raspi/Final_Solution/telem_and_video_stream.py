# This script does the following:
#	1) Record H264 Video using PiCam at a maximum bitrate of {bitrate_max} kbps
#	2) Record video data to a local BytesIO object
#	3) Send raw data over a TCP socket to a ground server
#	4) Store raw data to an onboard file
#	5) Clears BytesIO object after network stream and file store
#	6) Interrupts and ends recording after 'record_time' seconds

#	Client: RASPI
#	Server: COMPUTER

# Author: Ronnie Ankner
# Last Edited: 11/3/19
# Libraries
#	-> picamera -> PiCamera: Enables pi cam interfacing and settings manipulation
#	-> picamera -> PiCameraCircularIO: Allows for a circular buffer (if we want one)
#	-> threading: enables timer interrupt
#	-> io -> BytesIO : local file-like object that camera streams to
#	-> socket: allows for UDP socket and message sending
#	-> time: used to measure timing aspects of the system
#	-> os: runs terminal commands from python
#	-> sys: used exclusively for exiting the program


from picamera import PiCamera
from picamera import CircularIO
from io import BytesIO
import threading
import socket
import time
import os
import sys
import json
import serial
import struct

#======================= Global Variables and Objects =================
#Global Variables
vid_record_file = 'buffer_recording.h264' #on-board file video is stored to
bitrate_max = 200000 # bits per second
record_time = 10 # Time in seconds that the recording runs for
record_chunk = 0.2 #chunk size in seconds video object is broken into and sent 
frame_rate = 15 #camera frame rate
interrupt_bool = False #global interrupt flag that ends recording/program
store_and_send_bool = False #global interrupt flag that initiates sending and storing of camera data

#ensures chunk size is not smaller than one frame
if record_chunk < 1/frame_rate:
	record_chunk = 1/frame_rate

telem_record_file = 'telemtry_stream.txt'
baudrate = 115200
serial_port = "/dev/ttyACM0" #USB port
serial_port = "/dev/ttyAMA0" #UART serial pins PL011
#serial_port = "/dev/ttyS0" #UART serial pins miniUART

#Camera Settings
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = frame_rate

#Network Setup
SERVER_IP = '73.136.139.198'
SERVER_VIDEO_PORT = 5000
SERVER_TELEM_PORT = 5001

vid_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("RASPI CLIENT VIDEO Socket Created")
telem_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("RASPI CLIENT TELEMTRY Socket Created")

connected = [False, False]
connect_cnt = 0
while connect_cnt < 5:
	print("VIDEO connection attempt #%d"%(connect_cnt+1))
	try:
		vid_sock.connect((SERVER_IP, SERVER_VIDEO_PORT))
		print("RASPI CLIENT VIDEO Connected to COMPUTER SERVER!")
		connected[0] = True
		break
	except:
		connect_cnt += 1
		time.sleep(0.5)
connect_cnt = 0
while connect_cnt < 5:
	print("TELEMETRY connection attempt #%d"%(connect_cnt+1))
	try:
		telem_sock.connect((SERVER_IP, SERVER_TELEM_PORT))
		print("RASPI CLIENT TELEMTRY Connected to COMPUTER SERVER!")
		connected[1] = True
		break
	except:
		connect_cnt += 1
		time.sleep(0.5)
if (not(connected[0]) or not(connected[1])):
	print("One or more socket connections failed, Exiting")
	sys.exit()
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

def send_network(client_sock, msg):
	client_sock.sendall(msg)

def form_packet(JSON_obj):
	try:
		packet_info = JSON_obj["hdr"]
		packet_num = packet_info[0]
		time_stamp = packet_info[1]
		imu_data = JSON_obj["imu"]
		gps_data = JSON_obj["gps"]
		alt_data = JSON_obj["tpa"]
	except:
		return False
	
	all_data = [imu_data, gps_data, alt_data]

	packet_bytes = bytearray([192, 222]) #0xC0DE in hex (BEGINNING OF PACKET)
	packet_bytes += bytearray(struct.pack('>ii', packet_num, time_stamp))
	for data_lists in all_data:
		for data in data_lists:
			packet_bytes += bytearray(struct.pack(">f", data))
	packet_bytes += bytearray([237, 12]) #0xED0C in hex (END OF PACKET)
	
	return packet_bytes

def connect_to_teensy():
	connect_cnt = 0
	connected = False
	while (not(connected)):
		try:
			ser = serial.Serial(serial_port, baudrate)
			print("Teensy Connected!")
			connected = True
			return ser
		except:
			connect_cnt += 1 
			print("Trying to Connect: Attempt #%d"%(connect_cnt))
			time.sleep(0.5)
			if connect_cnt == 100:
				print("Teensy not found, Exiting")
				sys.exit()
#======================== Video Streaming and Recording ============
loop_cnt = 0.0
cnt = 0
#camera.start_preview()

#=================== Stores to local BytesIO then sends========================
#		    MOST EFFICENT AND TEST-PROVEN METHOD

#Initialize Video and Telemtry Buffers
stream = BytesIO()
telem_buff = BytesIO()

#Open and/or create onboard files to store video and telemetry
camera_file_handle = open(vid_record_file, 'wb+')
telem_file_handle = open(telem_record_file, 'wb+')

#Connect to Teensy
ser = connect_to_teensy()

print("Beginning Stream!")

#Begin Pi Cam recording
camera.start_recording(stream, format='h264', bitrate=bitrate_max)

vid_loop_sum = 0
vid_comms_sum = 0
vid_store_sum = 0
vid_max_packet = 0
vid_max_comms = 0

#Send Key word to Teensy to start dump
ser.write(b'dump')

#Start timer threads
threading.Timer(record_time, interrupt_func).start()
threading.Timer(record_chunk, store_interrupt_func).start()

program_start = time.time()

#Main Program Loop
while not(interrupt_bool):
	try:
		JSON_packet = ser.readline()
	except:
		print("Teensy Stream Interrupted")
		sys.exit()

	if (len(JSON_packet)):
		print("========================= TELEMETRY ============================")
		print("New Packet: %s"%(JSON_packet))
		if (JSON_packet.find(b'key word') != -1):
			ser.write(b'dump')
		corrupt = False
		try:
			JSON_obj = json.loads(JSON_packet)
		except:
			print("Error Creating JSON Obj; Invalid String")
			corrupt = True
			pass
		if (not(corrupt)):
			packet_Bytes = form_packet(JSON_obj)
			if (not(packet_Bytes)):
				print("ERROR: dirty little packet ;)")
			else:
				#telem_buff.write(packet_Bytes)
				packet_size = len(packet_Bytes)
				print("Current Packet | Size(%d):"%(packet_size))
				#print(packet_Bytes)
				telem_buff.write(packet_Bytes)
				telem_buff_size = telem_buff.getbuffer().nbytes
				print("Buffer | Size(%d):"%(telem_buff_size))
				if (telem_buff_size/packet_size >= 10):
					#Buffer Contains 10 telem Packets; store send and clear buffer

					#Store to file
					telem_file_handle.write(telem_buff.getvalue())
					
					#Send over the network
					send_network(telem_sock, telem_buff.getvalue())
					
					#Clear and Reset Buffer
					telem_buff.truncate(0)
					telem_buff.seek(0)
					print("Send and Saved %d Telemtry Bytes"%(telem_buff_size))
	
	#Camera Store and Send
	if (store_and_send_bool):
		print("========================= CAMERA ============================")
		threading.Timer(record_chunk, store_interrupt_func).start()
		loop_start = time.time()
		#executes when record_chunk thread times out
		#controls how often data is ported ofver the network and to file
		#change 'record_chunk' to vary time and data size
		
		#Reset global interrupt flag
		store_and_send_bool = False
		
		#Get Buffer Size:
		buff_size = stream.getbuffer().nbytes

		#Send bytes-like date over the Network (UDP)
		comms_start = time.time()
		send_network(vid_sock, stream.getvalue())
		comms_time = (time.time()-comms_start)
		vid_comms_sum += comms_time		
		
		#Store bytes-like data to file 
		store_start = time.time()
		camera_file_handle.write(stream.getvalue())
		vid_store_sum += (time.time()-store_start)

		#Clear local file-like object
		stream.truncate(0)
		stream.seek(0)

		#[Optional] Print Diagnostic printout
		cnt+=1
		print("Sent and Saved Chunk #%d | Loop Time: %f"%(cnt, (time.time()-loop_start)))
		#print("\tComms Time: %fs"%(vid_comms_time))
		print("\tData Size: %d Bytes | %d bits"%(buff_size, buff_size*8))
		#print("\tApparent Data Rate: %d kbps"%(float(buff_size*8)/(vid_comms_time*1000)))
		if buff_size > vid_max_packet:
			vid_max_packet = buff_size
		if comms_time > vid_max_comms:
			vid_max_comms = comms_time
		vid_loop_sum+=(time.time() - loop_start)
#======================================================================================

#End Recording and Tidy Up
total_time = time.time() - program_start 
print("Closing Connection")
vid_sock.close()
telem_sock.close()
print("Disconnecting from Teensy")
ser.close()
print("Ending Recording")
camera.stop_recording()
print("Closing Record Files")
camera_file_handle.close()
telem_file_handle.close()
print("Program Time:  %fs"%(total_time))
print("Video Process Time:  %fs | Video Process Usage: %f%%"%(vid_loop_sum, (vid_loop_sum*100)/total_time))
print("\tComms: %fs | %f%%\n\tStore: %fs | %f%%"%(vid_comms_sum, (vid_comms_sum*100)/vid_loop_sum, vid_store_sum,(vid_store_sum*100)/vid_loop_sum))
print("\tStream Metrics:\n\t\tMax Packet Size: %d Bytes\n\t\tMax Send Time  : %f ms"%(vid_max_packet, vid_max_comms*1000))

