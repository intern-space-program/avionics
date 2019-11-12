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
from numpy import array

# add nav directory to sys.path
sys.path.append("../../")
import nav.NavMain

home = '/home/pi'
store_dir = home + "/rocket_data"
cmd = "mkdir " + store_dir
os.system(cmd)

log_file = store_dir + "/system_log.txt"
log_handle = open(log_file, 'w')

def get_time():
	absolute_tm = time.localtime()
	ms = time.time()
	ms = ms - int(ms)
	return str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5]) + ":%.3f| "%(ms)

def log_start(msg):
	log_handle.write(("\n" + get_time() + msg))

absolute_tm = time.localtime()
time_str = "Script Started at " + str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5])
time_str += " on " + str(absolute_tm[1]) + "/" + str(absolute_tm[2]) + "/" + str(absolute_tm[0])

log_handle.write(time_str)

#============== MACROS ===============================
#Constant Macros
PI = 3.1415926535

#Network Macros
STREAM_READ = 1
STREAM_WRITE = 2

#================================== Networking Class =========================
class client_stream:
	def __init__(self, name, server_IP, server_port, read_store_file, write_store_file, mode):
		self.name = name
		self.server_IP = server_IP
		self.server_port = server_port
		self.socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.read_store_file = read_store_file
		self.write_store_file = write_store_file
		self.mode = mode #can be STREAM_READ, STREAM_WRTIE, or STREAM_READ|STREAM_WRITE
		self.alive = False
		self.read_file = False
		self.write_file = False
		self.print_output = True
		self.log_output = True
		
		if (mode & STREAM_READ == STREAM_READ):
			self.read_buffer = BytesIO() 
			self.read_file_handle = open(read_store_file, 'wb')
			self.read_file = True

		if (mode & STREAM_WRITE == STREAM_WRITE):
			self.write_buffer = BytesIO()
			self.write_file_handle = open(write_store_file, 'wb')
			self.write_file = True

		#Statistics [OPTIONAL]
		self.recv_packet_cnt = 0
		self.recv_total_bytes = 0
		self.send_packet_cnt = 0
		self.send_total_bytes = 0
	
	def __bool__(self):
		return self.alive
	
	def print_statistics(self):
		mode_name = ['STREAM_READ', 'STREAM_WRITE', 'STREAM_READ|STREAM_WRITE']
		print("Stream Name: %s"%(self.name))
		print("Stream Mode: %s"%(mode_name[self.mode-1]))
		print("Read:\n\tPackets:     %d\n\tTotal Bytes: %d"%(self.recv_packet_cnt, self.recv_total_bytes))
		print("Write:\n\tPackets:     %d\n\tTotal Bytes: %d"%(self.send_packet_cnt, self.send_total_bytes))

	def stream_print(self, msg):
		if (not(self.print_output)):
			return
		print("%s: %s"%(self.name, msg))

	def log_print(self, msg):
		if (not(self.log_output)):
			return
		log_start("%s: %s"%(self.name, msg))
	
	def connect_to_server(self):
		connect_cnt = 0
		self.log_print("Attempting to connect to server")
		while connect_cnt < 5:
			self.stream_print("Server connection attempt #%d"%(connect_cnt+1))
			try:
				self.socket_obj.connect_ex((self.server_IP, self.server_port))
				self.stream_print("Connection Successful")
				self.log_print("Connection Successful")
				self.alive = True
				break
			except:
				connect_cnt += 1

	def store_buffer(self, mode):
		if (mode & STREAM_READ == STREAM_READ):
			if (not(self.mode & STREAM_READ)):
				self.stream_print("READ ACCESS DENIED")
				return
			if(not(self.read_file)):
				return
			self.stream_print("Storing READ Buffer: %d Bytes"%(self.get_buffer_size(STREAM_READ)))
			self.read_file_handle.write(self.read_buffer.getvalue())

		if (mode & STREAM_WRITE == STREAM_WRITE):
			if (not(self.mode & STREAM_WRITE)):
				self.stream_print("WRITE ACCESS DENIED")
				return
			if(not(self.write_file)):
				return
			self.stream_print("Storing WRITE Buffer: %d Bytes"%(self.get_buffer_size(STREAM_WRITE)))
			self.write_file_handle.write(self.write_buffer.getvalue())
		
	def get_buffer_size(self, mode):
		if (mode & STREAM_READ == STREAM_READ):
			if (not(self.mode & STREAM_READ)):
				self.stream_print("NO READ BUFFER")
				return
			return self.read_buffer.getbuffer().nbytes

		if (mode & STREAM_WRITE == STREAM_WRITE):
			if (not(self.mode & STREAM_WRITE)):
				self.stream_print("NO WRITE BUFFER")
				return
			return self.write_buffer.getbuffer().nbytes

	def clear_buffer(self, mode):
		if (mode & STREAM_READ == STREAM_READ):
			if (not(self.mode & STREAM_READ)):
				self.stream_print("NO READ BUFFER")
				return
			if (self.get_buffer_size(STREAM_READ) == 0):
				return
			self.stream_print("Clearing READ Buffer")
			self.read_buffer.truncate(0)
			self.read_buffer.seek(0)

		if (mode & STREAM_WRITE == STREAM_WRITE):
			if (not(self.mode & STREAM_WRITE)):
				self.stream_print("NO WRITE BUFFER")
				return
			if (self.get_buffer_size(STREAM_WRITE) == 0):
				return
			self.stream_print("Clearing WRITE Buffer")
			self.write_buffer.truncate(0)
			self.write_buffer.seek(0)
	
	def close(self):
		self.stream_print("RUNNING FULL CLOSE")
		if (not(self.mode & STREAM_READ)):
			pass
		else:
			self.store_buffer(STREAM_READ)
			self.clear_buffer(STREAM_READ)
			self.close_file(STREAM_READ)

		if (not(self.mode & STREAM_WRITE)):
			pass
		else:
			if (self.get_buffer_size(STREAM_WRITE) > 0):
				self.send_packet(self.write_buffer.getvalue())
			self.store_buffer(STREAM_WRITE)
			self.clear_buffer(STREAM_WRITE)
			self.close_file(STREAM_WRITE)

		self.close_socket()
	
	def close_socket(self):
		if (not(self.alive)):
			return
		self.alive = False
		self.stream_print("Closing Socket")
		self.socket_obj.close()
	
	def close_file(self, mode):
		if (mode & STREAM_READ == STREAM_READ):
			if (not(self.mode & STREAM_READ)):
				self.stream_print("READ ACCESS DENIED")
				return
			if(not(self.read_file)):
				return
			self.stream_print("Closing READ File")
			self.read_file_handle.close()
			self.read_file = False

		if (mode & STREAM_WRITE == STREAM_WRITE):
			if (not(self.mode & STREAM_WRITE)):
				self.stream_print("WRITE ACCESS DENIED")
				return
			if(not(self.write_file)):
				return
			self.stream_print("Closing WRITE File")
			self.write_file_handle.close()
			self.write_file = False
	
	def add_to_buffer(self, msg, mode):
		if (mode & STREAM_READ == STREAM_READ):
			if (not(self.mode & STREAM_READ)):
				self.stream_print("NO READ BUFFER")
				return
			self.stream_print("Adding to READ Buffer")
			self.read_buffer.write(msg)

		if (mode & STREAM_WRITE == STREAM_WRITE):
			if (not(self.mode & STREAM_WRITE)):
				self.stream_print("NO WRITE BUFFER")
				return
			self.stream_print("Adding to WRITE Buffer")
			self.write_buffer.write(msg)
	
	def send_packet(self, msg):
		if (not(self.alive)):
			return
		transmitted = False
		self.stream_print("Running SEND_PACKET")
		if (not(self.mode & STREAM_WRITE)):
			self.stream_print("WRITE ACCESS DENIED")
		else:
			try:
				self.send_packet_cnt += 1
				self.send_total_bytes += len(msg)
				self.socket_obj.sendall(msg)
				self.stream_print("Packet %d | Size (%d) Sent successfully"%(self.send_packet_cnt, len(msg)))
				transmitted = True
			except:
				self.stream_print("ERROR Sending Message, closing socket")
				self.log_print("ERROR Sending Message, closing socket")
				self.close_socket()
				
		
	def recv_new_packet(self):
		if (not(self.alive)):
			return
		if (not(self.mode & STREAM_READ)):
			self.stream_print("READ ACCESS DENIED")
		else:
			packet = self.socket_obj.recv(4096)
			if (not(packet)):
				self.stream_print("Stream ended, storing, then closing connection and file")
				self.log_print("Stream ended, storing, then closing connection and file")
				self.close_socket()
				return
			print("%s: New Packet | Size: %d Bytes"%(self.name, len(packet)))
			self.read_buffer.write(packet)
			self.recv_packet_cnt += 1
			self.recv_total_bytes += len(packet)

#================================== Serial Class =========================
class teensy_handle:
	
	def __init__(self):
		self.baudrate = 115200
		#self.serial_port = '/dev/ttyACM0' #USB serial
		self.serial_port = '/dev/ttyAMA0' #Serial pins TX/RX -> 14/15
		self.ser = None
		self.status = [0,0,0] #teensy, imu, gps, alt
		self.connected = False
		self.alive = False
		self.print_output = True
		self.log_output = True
		
	def __bool__(self):
		return self.alive
	
	def stream_print(self, msg):
		if (not(self.print_output)):
			return
		print("TEENSY: %s"%(msg))

	def log_print(self, msg):
		if (not(self.log_output)):
			return
		log_start("TEENSY: %s"%(msg))

	def connect(self):
		connect_cnt = 0
		while (not(self.connected)):
			try:
				self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=0.1)
				self.connected = True
				self.stream_print("Connected!")
				self.log_print("Connected!")
			except:
				connect_cnt += 1 
				self.stream_print("Trying to Connect: Attempt #%d"%(connect_cnt))
				if connect_cnt > 10:
					self.stream_print("Not found, Unable to Connect")
					self.log_print("Not found, Unable to Connect")
					return


	def start_up(self):
		if (not(self.connected)):
			return
		starting = False
		self.stream_print("Starting Startup")
		for i in range(0,5):
			self.stream_print('Start_up Attempt %d'%(i))
			self.ser.write(b'startup')
			resp = self.ser.readline()
			if b'starting' in resp:
				starting = True
				break
		if (not(starting)):
			self.stream_print("ERROR Teensy never heard startup")
			self.log_print("ERROR Teensy never heard startup")
			return
		resp = b''
		self.stream_print("Started and waiting for initialized from teensy")
		start = time.time()
		while(not(b'initialized' in resp)):
			#do error analysis of output in here
			resp = self.ser.readline()
			if resp:
				self.stream_print(resp)
			if time.time()-start > 10:
				self.log_print("ERROR Teensy Watch Dog Timed out")
				self.stream_print("ERROR Teensy Watch Dog Timed out")
				return
		self.stream_print("Teensy successfully started")
		self.log_print("Teensy successfully started")
		self.alive = True

	def start_stream(self):
		if (not(self.connected)):
			return
		self.stream_print("Beginning JSON Stream")
		self.log_print("Beginning JSON Stream")
		self.ser.write(b'dump')

	def read_in_json(self):
		if (not(self.connected)):
			return
		JSON_packet = b''
		try:
			JSON_packet = self.ser.readline()
		except:
			self.alive = False

		if (len(JSON_packet)):
			self.stream_print("New Packet: %s"%(JSON_packet))
			if (JSON_packet.find(b'dump_init') != -1):
				self.alive = False
				for i in range(0,3):
					self.ser.write(b'startup')
			if (JSON_packet.find(b'initialized') != -1):
				self.ser.write(b'dump')
				self.alive = True
			corrupt = False
			try:
				JSON_obj = json.loads(JSON_packet)
			except:
				self.stream_print("Error Creating JSON Obj; Invalid String")
				corrupt = True
				pass
			if (not(corrupt)):
				return JSON_obj
			else:
				return False
		

#======================= Global Variables and Objects =================
vid_record_file = store_dir + '/video_stream.h264' #on-board file video is stored to
telem_record_file = store_dir + '/telemtry_stream.txt'
bitrate_max = 200000 # bits per second
record_time = 30 # Time in seconds that the recording runs for
record_chunk = 0.12 #chunk size in seconds video object is broken into and sent 
frame_rate = 15 #camera frame rate
interrupt_bool = False #global interrupt flag that ends recording/program
store_and_send_bool = False #global interrupt flag that initiates sending and storing of camera data


#ensures chunk size is not smaller than one frame
if record_chunk < 1/frame_rate:
	record_chunk = 1/frame_rate

#Camera Settings
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = frame_rate

#Network Settings
SERVER_IP = '73.136.139.198'
#SERVER_IP = '192.168.0.108'
SERVER_VIDEO_PORT = 5000
SERVER_TELEM_PORT = 5001

video_stream = client_stream("VIDEO", SERVER_IP, SERVER_VIDEO_PORT, None, vid_record_file, STREAM_WRITE)
telem_stream = client_stream("TELEMETRY", SERVER_IP, SERVER_TELEM_PORT, None, telem_record_file, STREAM_WRITE)

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

def get_new_state(current_state, JSON_packet, previous_millis):
	time_diff = JSON_packet["hdr"][1] - previous_millis
	if time_diff > 500:
		return current_state
	else:
		time_diff = float(time_diff)/1000.0

	imu_data = JSON_obj["imu"]
	gps_data = JSON_obj["gps"]
	alt_data = JSON_obj["tpa"]

	altitude = float(alt_data[2])
	
	#convert JSON_packet to python dict
	sensor_readings = {
		"time": time_diff,
		"altitude": altitude,
		"gps": array(gps_data),
		"accel_nc": array(imu_data[7:10]),
		"accel_c": array(imu_data[0:3]),
		"angular_velocity": array(imu_data[13:16]),
		"q_inert_to_body": array(imu_data[3:7])
	}

	#recieve updated state
	updated_state = nav.NavMain.main(current_state, sensor_readings)

	#return updated state
	return updated_state

def form_bin_packet(current_state):
	#take in current state dict
	#form binary packet
	#return binary packet/
	pass
	
#======================== Video/Telemetry Streaming and Recording ============
loop_cnt = 0.0
cnt = 0

#Navigation Variables
current_state = {
	"time":0.0, 
	"position":array([0.0, 0.0, 0.0]),
	"velocity":array([0.0, 0.0, 0.0]),
	"attitude":array([1.0, 0.0, 0.0, 0.0])
}

previous_millis = 0

#Connect to Server
video_stream.connect_to_server()
telem_stream.connect_to_server()

#Connect to Teensy and do hand shake
teensy = teensy_handle()
teensy.connect()
teensy.start_up()

#Begin Pi Cam recording
camera.start_recording(video_stream.write_buffer, format='h264', bitrate=bitrate_max)

#Start timer threads
threading.Timer(record_time, interrupt_func).start()
threading.Timer(record_chunk, store_interrupt_func).start()

#=================================== Offical Beginning of Stream -> Do all setup before this =============
#Start dump of data from Teensy:
teensy.start_stream()

program_start = time.time()

#Main Program Loop
while not(interrupt_bool):

	new_JSON = teensy.read_in_json()
	packet_Bytes = False
	if (not(new_JSON)):
		pass
	else:
		current_state = get_new_state(current_state, new_JSON)
		previous_millis = new_JSON["hdr"][1]
		packet_Bytes = form_bin_packet(current_state)
		
	if (packet_Bytes):
		#New Telemetry Data: Add to the buffer
		telem_stream.add_to_buffer(packet_Bytes, STREAM_WRITE)
		
		#If buffer gets to a certain size, send and store
		packet_size = len(packet_Bytes)
		if (telem_stream.get_buffer_size(STREAM_WRITE)/packet_size > 10):
			#Send Buffer over Network
			if (telem_stream):
				telem_stream.send_packet(telem_stream.write_buffer.getvalue())
			else:
				telem_stream.connect_to_server()
			
			#Store Buffer to File
			telem_stream.store_buffer(STREAM_WRITE)
			
			#Clear Buffer
			telem_stream.clear_buffer(STREAM_WRITE)
		

	#Camera Store and Send
	if (store_and_send_bool):
		#Reset Timer
		threading.Timer(record_chunk, store_interrupt_func).start()

		#Reset global interrupt flag
		store_and_send_bool = False
		
		#Send Video Data over Network
		if (video_stream):
			video_stream.send_packet(video_stream.write_buffer.getvalue())
		else:
			video_stream.connect_to_server()

		#Store Data to File
		video_stream.store_buffer(STREAM_WRITE)

		#Clear Buffer
		video_stream.clear_buffer(STREAM_WRITE)
		

#======================================================================================

#End Recording and Tidy Up
total_time = time.time() - program_start
log_start("Stream Ended, Closing sockets and files")
video_stream.close()
telem_stream.close()

video_stream.print_statistics()
telem_stream.print_statistics()

absolute_tm = time.localtime()
time_str = "\nScript Ended at " + str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5])
time_str += " on " + str(absolute_tm[1]) + "/" + str(absolute_tm[2]) + "/" + str(absolute_tm[0])

log_handle.write(time_str)

log_handle.close() 

