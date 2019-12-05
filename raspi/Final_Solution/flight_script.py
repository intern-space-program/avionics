#TODO: UDPATE THIS HEADER -> THIS IS NOT CORRECT 
#This script does the following:
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
import selectors
import subprocess
from gpiozero import LED

# add nav directory to sys.path
sys.path.append("/home/pi/Intern_Space_Program_Git/F2019_Avionics/")
import nav.NavMain

LTE_led = LED(13)
SERVER_led = LED(5)
RECORDING_led = LED(6)

cnt = 0
while cnt < 10:
	cnt += 1
	LTE_led.on()
	SERVER_led.on()
	RECORDING_led.on()
	time.sleep(0.5)
	LTE_led.off()
	SERVER_led.off()
	RECORDING_led.off()
	time.sleep(0.5)
cnt = 0
while cnt < 10:
	cnt += 1
	LTE_led.on()
	time.sleep(0.2)
	LTE_led.off()
	SERVER_led.on()
	time.sleep(0.2)
	SERVER_led.off()
	RECORDING_led.on()
	time.sleep(0.2)
	RECORDING_led.off()
	SERVER_led.on()
	time.sleep(0.2)
	SERVER_led.off()


home = '/home/pi'
store_dir = home + "/rocket_data"
cmd = "mkdir " + store_dir
os.system(cmd)

log_file = store_dir + "/system_log.txt"

def get_time():
	absolute_tm = time.localtime()
	ms = time.time()
	ms = ms - int(ms)
	return str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5]) + ":%.3f| "%(ms)

def log_start(msg):
	with open(log_file, 'a') as log_writer:
		log_writer.write(("\n" + get_time() + msg))

absolute_tm = time.localtime()
time_str = "Script Started at " + str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5])
time_str += " on " + str(absolute_tm[1]) + "/" + str(absolute_tm[2]) + "/" + str(absolute_tm[0])

log_handle = open(log_file, 'w')
log_handle.write(time_str)
log_handle.close()

#================================= CONFIGURE NETWORK ==========================================
#Ouput messages
not_connected_msg = "ERROR: Modem not detected"
fail_msg = "Failed to start PPP"
success_msg = "PPP session started"

LTE_led.blink()
LTE_connected = False
os.system("sudo hologram network disconnect -v")#make sure PPP connection does not exist
LTE_timeout = 300 #5 minute timout
LTE_start = time.time()
while (not(LTE_connected)):
	if (time.time()-LTE_start)>LTE_timeout:
		log_start("LTE CONNECTION ATTEMPT TIMED OUT")
		break
	log_start("Running Hologram Connect")
	#print("Running Hologram Connect")
	#Begin a subprocess to start PPP connection and connect LTE network
	LTE_connect = subprocess.Popen(['sudo', 'hologram', 'network', 'connect', '-v'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	while True:
		out, err = LTE_connect.communicate()
		output = str(out + err)
		if output.find(not_connected_msg) != -1 :
			log_start("Modem Disconnected")
			break
		elif output.find(fail_msg) != -1 :
			log_start("Connection Failed")
			break
		elif output.find(success_msg) != -1:
			log_start("CONNECTION SUCCEEDED")
			#print("CONNECTION SUCCEEDED")
			LTE_led.on()
			LTE_connected = True
			break
		elif (len(output) == 0):
			log_start("Program Failed")
			break
		else:
			log_start("Undetermined Error, Exiting")

#Once LTE is connected, 
os.system("sudo ifconfig wlan0 down") #disable wifi
if (not(LTE_connected)):
	LTE_led.off()

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
		self.socket_obj.settimeout(3)
		self.read_store_file = read_store_file
		self.write_store_file = write_store_file
		self.mode = mode #can be STREAM_READ, STREAM_WRTIE, or STREAM_READ|STREAM_WRITE
		self.alive = False
		self.read_file = False
		self.write_file = False
		self.print_output = False
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
		if (not(self.print_output)):
			return
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
	
	def force_bytes(self, msg):
		if isinstance(msg, bytes):
			return msg
		elif isinstance(msg, str):
			return msg.encode('utf-8')
		elif isinstance(msg, int):
			return struct.pack('>i', msg)
		elif isinstance(msg, float):
			return struct.pack('>f', msg)
		elif isinstance(msg, bool):
			return struct.pack('>?', msg)
		else:
			return None
	
	def register_with_server(self):
		if not(self.alive):
			return
		self.stream_print("Registering with server")
		self.log_print("Registering with server")
		if (self.name == 'VIDEO'):
			
			self.send_packet(b'vid src')
		if (self.name == 'TELEMETRY'):
			self.send_packet(b'telem src')
		self.send_packet(b'im alive')

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
		self.register_with_server()
	
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
			msg = self.force_bytes(msg)
			if msg is None:
				self.stream_print("ERROR BAD DATA TYPE: NOT SERIALIZABLE -> Packet not sent")
				return
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
			return None
		if (not(self.mode & STREAM_READ)):
			self.stream_print("READ ACCESS DENIED")
		else:
			packet = self.socket_obj.recv(4096)
			if (not(packet)):
				self.stream_print("Stream ended, storing, then closing connection and file")
				self.log_print("Stream ended, storing, then closing connection and file")
				self.close_socket()
				return None
			search = "KILL STREAM"
			if packet.find(search.encode('utf-8')) != -1:
				self.stream_print("KILL statement heard, doing full close")
				self.log_print("KILL statement heard, doing full close")
				return "kill"
			self.stream_print("%s: New Packet | Size: %d Bytes"%(self.name, len(packet)))
			self.read_buffer.write(packet)
			self.recv_packet_cnt += 1
			self.recv_total_bytes += len(packet)
			return None


	def wait_for_start(self, time_out):
		start = time.time()
		time_diff = time.time()-start
		sel = selectors.DefaultSelector()
		events = selectors.EVENT_READ|selectors.EVENT_WRITE
		sel.register(self.socket_obj, events, data="onlyDamnSocket")
		last_time = int(time_out)
		while(time_diff < time_out):
			events = sel.select(timeout = 1.0)
			for key, mask in events:
				if key.data == "onlyDamnSocket" and mask == selectors.EVENT_READ|selectors.EVENT_WRITE:
					self.stream_print("EVENT FOUND") 
					packet = self.socket_obj.recv(4096)
					if (not(packet)):
						self.stream_print("Stream ended, storing, then closing connection and file")
						self.log_print("Stream ended, storing, then closing connection and file")
						self.close_socket()
						return
					search = "turn you on"
					self.stream_print("Packet Has data") 
					if packet.find(search.encode('utf-8')) != -1:
						self.stream_print("STARTUP FOUND!")
						return
			time_diff = time.time()-start
			if int(time_diff) != last_time:
				msg = "Time left till automatic start; %.2f"%(time_out-time_diff)
				self.stream_print(msg)
				self.send_packet(msg.encode('utf-8'))
				last_time = int(time_diff)
		return
			

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
		self.print_output = False
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
				return True
			except:
				connect_cnt += 1 
				self.stream_print("Trying to Connect: Attempt #%d"%(connect_cnt))
				if connect_cnt > 10:
					self.stream_print("Not found, Unable to Connect")
					self.log_print("Not found, Unable to Connect")
					return False


	def start_up(self, time_out):
		if (not(self.connected)):
			return
		starting = False
		self.stream_print("Starting Startup")
		resp = b''
		for i in range(0,5):
			self.ser.write(b'startup')
			resp = self.ser.readline()
			if resp.find(b'starting') != -1:
				starting = True
				break
		if (not(starting)):
			self.stream_print("ERROR Teensy never heard startup")
			self.log_print("ERROR Teensy never heard startup")
			return
		resp = b''
		self.stream_print("Started and waiting for initialized from teensy")
		start = time.time()
		while(resp.find(b'initialized')):
			#do error analysis of output in here
			resp = self.ser.readline()
			if resp:
				self.stream_print(resp)
			if time.time()-start > time_out:
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
			return None
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
				self.alive = True
				return JSON_obj
			else:
				return None

#TODO Create rocket class to record information and inform system operation
#keep track of: 
#	max speed(resultant and DOF)
#	max acc(resultant and DOF)
#	max_height, height
#	whether it is back on the ground AGAIN
#	timesince on the ground	

#======================= Global Variables and Objects =================
vid_record_file = store_dir + '/video_stream.h264' #on-board file video is stored to
telem_record_file = store_dir + '/telemtry_stream.txt'
telem_cmd_file = store_dir + '/telemetry_cmds.txt'
bitrate_max = 120000 # bits per second
record_time = 60 # Time in seconds that the recording runs for
record_chunk = 0.12 #chunk size in seconds video object is broken into and sent 
frame_rate = 15 #camera frame rate
interrupt_bool = False #global interrupt flag that ends recording/program
store_and_send_bool = False #global interrupt flag that initiates sending and storing of camera data


#ensures chunk size is not smaller than one frame
if record_chunk < 1/frame_rate:
	record_chunk = 1/frame_rate

#Camera Settings
camera_alive = False
try:
	camera = PiCamera()
	camera_alive = True
except:
	#print("CAMERA NOT CONNECTED")
	log_start("CAMERA NOT CONNECTED")

if (camera_alive):
	camera.resolution = (640, 480)
	camera.framerate = frame_rate

#Network Settings
SERVER_IP = '73.136.139.198'
SERVER_IP = '73.115.48.151'
SERVER_VIDEO_PORT = 5000
SERVER_TELEM_PORT = 5001

#Create stream objects for video and telemetry
#def __init__(self, name, server_IP, server_port, read_store_file, write_store_file, mode):
video_stream = client_stream("VIDEO", SERVER_IP, SERVER_VIDEO_PORT, None, vid_record_file, STREAM_WRITE)
telem_stream = client_stream("TELEMETRY", SERVER_IP, SERVER_TELEM_PORT, telem_cmd_file, telem_record_file, STREAM_WRITE|STREAM_READ)

#Create Selector object to allow for non-blocking read of telemetry port
main_sel = selectors.DefaultSelector()
telem_events = selectors.EVENT_READ|selectors.EVENT_WRITE
main_sel.register(telem_stream.socket_obj, telem_events, data="Telem_upstream")

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

def get_new_state(current_state, JSON_packet, previous_millis):
	time_diff = JSON_packet["hdr"][1] - previous_millis
	if time_diff > 500: 
		#integer value is number of milliseconds since the last observation: 
		#New samples should come every 100ms 
		#buffer of 500ms is there to protect from bogus values (and hence state propogation) from first packet, or first packet after long drop out
		#therefore, if it is greater, ignore this packet and return the same state
		return current_state
	else:
		time_diff = float(time_diff)/1000.0

	imu_data = JSON_packet["imu"]
	gps_data = JSON_packet["gps"]
	alt_data = JSON_packet["tpa"]

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

def form_bin_packet(current_state, packet_cnt, status_list):
	#take in current state dict
	MET = current_state["time"]	
	position = current_state["position"]
	velocity = current_state["velocity"]
	attitude = current_state["attitude"]
	
	#form binary packet
	packet_bytes = bytearray([192, 222]) #0xC0DE in hex (BEGINNING OF PACKET)
	packet_bytes += bytearray(struct.pack('>if', packet_cnt, MET))
	packet_bytes += bytearray(struct.pack('>???????', status_list[0], status_list[1],status_list[2],status_list[3],status_list[4],status_list[5],status_list[6]))
	packet_bytes += bytearray(struct.pack('>fff', position[0], position[1], position[2]))
	packet_bytes += bytearray(struct.pack('>fff', velocity[0], velocity[1], velocity[2]))
	packet_bytes += bytearray(struct.pack('>ffff', attitude[0], attitude[1], attitude[2], attitude[3]))
	packet_bytes += bytearray([237,12]) #0xED0C in hex (END OF PACKET)
	
	#return binary packet
	return packet_bytes

def populate_status_list(status_list, JSON_packet, telem_stream_alive, video_stream_alive):
	#IMU, GPS, ALT, Teensy, Raspi, LTE, Serial
	if JSON_packet is not(None):
		status_list[0] = JSON_packet['hdr'][4] #IMU
		status_list[1] = JSON_packet['hdr'][2] #GPS
		status_list[2] = JSON_packet['hdr'][3] #ALT
		status_list[3] = True
	else:
		status_list[0] = False
		status_list[1] = False
		status_list[2] = False
		status_list[3] = False
	
	if (telem_stream_alive or video_stream_alive):
		status_list[5] = True
		SERVER_led.on()
	else:
		SERVER_led.off()
		status_list[5] = False
	
#======================== Video/Telemetry Streaming and Recording ============
loop_cnt = 0.0
cnt = 0

#Navigation Variables
current_state = {
	"time": 0.0, 
	"position":array([0.0, 0.0, 0.0]),
	"velocity":array([0.0, 0.0, 0.0]),
	"attitude":array([1.0, 0.0, 0.0, 0.0])
}
status_list = [False, False, False, False, False, False, False] #IMU, GPS, ALT, Teensy, Raspi, LTE, Serial
previous_millis = 0

#Connect to Server
SERVER_led.blink()
video_stream.connect_to_server()
telem_stream.connect_to_server()

#Connect to Teensy and do hand shake
teensy = teensy_handle()
status_list[6] = teensy.connect()
teensy.start_up(31)

status_list[4] = True
populate_status_list(status_list, None, telem_stream.alive, video_stream.alive)

RECORDING_led.blink()

#Wait for startup signal from server
if (telem_stream.alive):
	telem_stream.wait_for_start(8*60) #value here is the timeout


#log_start("Waited 3 seconds")
log_start("STARTING STREAM")	
RECORDING_led.on()
#log_start("turned led on")

#=================================== Offical Beginning of Stream -> Do all setup before this =============
#Begin Pi Cam recording
if camera_alive:
	camera.start_recording(video_stream.write_buffer, format='h264', bitrate=bitrate_max)
	log_start("Starting Camera Stream")
#Start timer threads
#threading.Timer(record_time, interrupt_func).start()
threading.Timer(record_chunk, store_interrupt_func).start()

#Start dump of data from Teensy:
teensy.start_stream()

program_start = time.time()
program_timeout = 15*60

err_cnt = 0
#Main Program Loop
while not(interrupt_bool): #TODO while (telem_stream or video_stream or {rocket has been up and back down to the ground for a significant amount of time} maybe use a class to carry this out	
	err_cnt += 1
	#log_start("Looping %d"%(err_cnt))
	if (time.time()-program_start) > program_timeout:
		interrupt_bool = True
	if (telem_stream.alive or video_stream.alive):
		SERVER_led.on()
	else:
		SERVER_led.off()

	#Look at selector for any events then move on to rest:
	events = main_sel.select(timeout=0.05)
	for key, mask in events:
		if ((key.data == "Telem_upstream") and (mask == selectors.EVENT_READ|selectors.EVENT_WRITE)):
			res = telem_stream.recv_new_packet()
			if isinstance(res, str):
				if res == "kill":
					print("KILL SWITCH RECIEVED -> CLOSING STREAMS AND ENDING PROGRAM")
					interrupt_bool = True
	
	#pull in new packet from teensy (TIMEOUT IS EVERY 0.1 SECONDS SO THIS WILL BLOCK FOR AT LEAST 0.1s)
	new_JSON = teensy.read_in_json()
	packet_Bytes = False
	if (new_JSON is None):
		populate_status_list(status_list, new_JSON, telem_stream.alive, video_stream.alive)
		packet_Bytes = form_bin_packet(current_state,0, status_list)
	else:
		#New JSON from teensy -> use information to propagate state and any other essential values
		current_state = get_new_state(current_state, new_JSON, previous_millis)
		previous_millis = new_JSON["hdr"][1]
		populate_status_list(status_list, new_JSON, telem_stream.alive, video_stream.alive)
		packet_Bytes = form_bin_packet(current_state, new_JSON["hdr"][0], status_list)
		
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
	# -> operates on global bool which is flipped by timer
	# -> timer goes off every {record_chunk}s
	# -> should be a little less than the serial timeout + selector timeout
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
#check to see if telem stream or video stream are still open, and if so close/echo kill
if (video_stream):
	video_stream.send_packet(b'KILL STREAM')
	video_stream.close()
if (telem_stream):
	video_stream.send_packet(b'KILL STREAM')
	video_stream.close()
RECORDING_led.off()
SERVER_led.off()
#End Recording and Tidy Up
total_time = time.time() - program_start
log_start("Stream Ended, Closing sockets and files")

video_stream.print_statistics()
telem_stream.print_statistics()

absolute_tm = time.localtime()
time_str = "\nScript Ended at " + str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5])
time_str += " on " + str(absolute_tm[1]) + "/" + str(absolute_tm[2]) + "/" + str(absolute_tm[0])

log_start(time_str)

os.system("sudo hologram network disconnect -v")#make sure PPP connection does not exist
LTE_led.off()

