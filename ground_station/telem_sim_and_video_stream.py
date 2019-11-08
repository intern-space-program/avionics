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
from math import sin
from math import cos
from math import sqrt
import math
import threading
import socket
import time
import os
import sys
import json
import serial
import struct
#======================= TRAJECTORY SIMULATION CODE =================

#============== MACROS ===============================

#state variable 'macros'
ZEROTH_ORDER = 0
FIRST_ORDER = 1
SECOND_ORDER = 2

X = 0
Y = 1
Z = 2

#Constant Macros
PI = 3.1415926535


#============== CLASSES ===============================

class model_params:

	def __init__(self):
		self.max_phi = 0.524 #radians (about 30 degrees)
		self.max_phi_accel = 0.1 # rad/s/time_step
		self.max_theta_accel = 0.1 #rad/s/time_step
		self.time_step = 0.01 #seconds
		self.gravity = 9.8 #m/s^2 

class rocket:

	def __init__(self, start_v, start_a, start_phi, start_theta):

		#Rocket Frame Variables
		self.velocity = start_v #(m/s) magnitude which always points in direction of rocket
		self.accel = start_a #(m/s^2) magnitude which always points in direction of rocket
		#rocket_pos = [0, start_v, start_a] # (m, m/s, m/s^2) 3 DOF magnitude list | 0th is flight path distance, 1st is vel magnitude, 2nd is accel magnitude
		self.phi = [start_phi, 0, 0] #(radians) 3 order list | 0th order phi is clockwise angle from Z axis
		self.theta = [start_theta, 0, 0] #(radians) 3 order list | 0th order theta is clockwise angle from X axis
		self.thrust = 0.0 # (Newtons) magnitude force always in direction of the rocket

		#Rocket model properties
		self.mass = 1 #(kg)
		self.drag_const  = 0.01 #0.5*Cd*A*p all lumped together | reasonable is around 0.01 or less

		#Overall Inertial Frame Variables
		self.position = [[0,0,0],[0,0,0],[0,0,0]] # (m, m/s, m/s^2) 9DOF freedom position: 3DOF position, 3DOF velocity, 3DOF accel
		self.position_name = ["Position", "Velocity", "Acceleration"]
		self.angle = [[0,0,0],[0,0,0],[0,0,0]] # (rad, rad/s, rad/s^2) 9DOF freedom angle: 3DOF angle, 3DOF angular velocity, 3DOF angular acceleration
		self.angle_name = ["Angle", "Angular Velocity", "Angular Acceleration"]
		self.overall_time = 0.0

		#Flight Metrics
		self.max_height = 0
		self.max_speed = 0
		self.max_velocity = 0
		self.max_acceleration_mag = 0
		self.max_acceleration_DOF = 0
		self.flight_time = 0
		self.distance_from_pad = 0

		self.model = model_params()
		self.print_each_step = False
		self.packet_cnt = 0

	def __bool__(self):
		if self.position[ZEROTH_ORDER][Z] > -0.001:
			return True
		else:
			return False

	def transpose_ground_frame_to_rocket_frame(self):
		self.velocity = sqrt(math.pow(self.position[FIRST_ORDER][X],2)+math.pow(self.position[FIRST_ORDER][Y],2)+math.pow(self.position[FIRST_ORDER][Z],2))
		self.accel = sqrt(math.pow(self.position[SECOND_ORDER][X],2)+math.pow(self.position[SECOND_ORDER][Y],2)+math.pow(self.position[SECOND_ORDER][Z],2))

		for order in range(0,3):
			self.phi[order] = math.acos(angle[order][Z])
			if (angle[order][Y] >= 0):
				self.theta[order] = math.acos(angle[order][X]/sin(self.phi[order]))
			if (angle[order][Y] < 0):
				self.theta[order] = 2*PI - math.acos(angle[order][X]/sin(self.phi[order]))

	def transpose_rocket_frame_to_ground_frame(self):

		for order in range(0,3):
			self.angle[order][Z] = cos(self.phi[order])
			self.angle[order][X] = sin(self.phi[order])*cos(self.theta[order])
			self.angle[order][Y] = sin(self.phi[order])*sin(self.theta[order])

		for DOF in range(0,3):
			self.position[FIRST_ORDER][DOF] = self.velocity*self.angle[ZEROTH_ORDER][DOF]
			self.position[SECOND_ORDER][DOF] = self.accel*self.angle[ZEROTH_ORDER][DOF]

		"""self.position[FIRST_ORDER][Z] = self.velocity*cos(self.phi[ZEROTH_ORDER])
		self.position[FIRST_ORDER][X] = self.velocity*sin(self.phi[ZEROTH_ORDER])cos(self.theta[ZEROTH_ORDER])
		self.position[FIRST_ORDER][Z] = self.velocity*sin(self.phi[ZEROTH_ORDER])sin(self.theta[ZEROTH_ORDER]) 
		self.position[SECOND_ORDER][Z] = self.accel*cos(self.phi[ZEROTH_ORDER])
		self.position[SECOND_ORDER][X] = self.accel*sin(self.phi[ZEROTH_ORDER])cos(self.theta[ZEROTH_ORDER])
		self.position[SECOND_ORDER][Z] = self.accel*sin(self.phi[ZEROTH_ORDER])sin(self.theta[ZEROTH_ORDER])"""

	def print_position_vec(self, order):
		print("%s:\n\tX: %f | Y: %f | Z: %f"%(self.position_name[order], self.position[order][X], self.position[order][Y], self.position[order][Z]))

	def print_angle_vec(self, order):
		print("%s:\n\tX: %f | Y: %f | Z: %f"%(self.angle_name[order], self.angle[order][X], self.angle[order][Y], self.angle[order][Z]))

	def print_rocket_frame(self):
		print("Positional:\n\tVelocity:     %f\n\tAcceleration: %f"%(self.velocity, self.accel))
		print("Angular:\n\tPhi:   %f | %f\n\tTheta: %f | %f"%(self.phi[ZEROTH_ORDER], (self.phi[ZEROTH_ORDER]*180/PI), self.theta[ZEROTH_ORDER], (self.theta[ZEROTH_ORDER]*180/PI)))

	def print_flight_metrics(self):
		print("=============Flight Statistics ============")
		print("Max Height:              %f m"%(self.max_height))
		print("Max Speed:               %f m/s"%(self.max_speed))
		print("Max Velocity:            %f m/s"%(self.max_velocity))
		print("Max Acceleration(mag):   %f m/s^2"%(self.max_acceleration_mag))
		print("Max Acceleration(DOF):   %f m/s^2"%(self.max_acceleration_DOF))
		print("\nFlight Time:             %f s"%(self.flight_time))
		print("Distance from Pad:       %f m"%(self.distance_from_pad))

	def time_step_print(self):
		print("Time: %f"%(self.overall_time))
		for order in range(0,3):
			self.print_position_vec(order)
			self.print_rocket_frame()
		print("----------------------------------------------------------------------------")
		time.sleep(5*self.model.time_step)
	
	def form_bin_packet(self):
		if (int(self.overall_time*100)%10 == 0):
			print("New Packet at time: %f | %d"%(self.overall_time, int(self.overall_time*100)%10))
			self.packet_cnt += 1
			packet_bytes = bytearray([192, 222]) #0xC0DE in hex (BEGINNING OF PACKET)
			packet_bytes += bytearray(struct.pack('>ii', self.packet_cnt, int(self.overall_time*100)))
			packet_bytes += bytearray(struct.pack('>???????', 1,0,1,1,0,1,1))
			packet_bytes += bytearray(struct.pack('>fff', self.position[0][0], self.position[0][1], self.position[0][2]))
			packet_bytes += bytearray(struct.pack('>fff', self.position[1][0], self.position[1][1], self.position[1][2]))
			packet_bytes += bytearray(struct.pack('>fff', self.angle[0][0], self.angle[0][1], self.angle[0][2]))
			packet_bytes += bytearray([237,12]) #0xED0C in hex (END OF PACKET)
			return packet_bytes
		else:
			return False

	def update_metrics(self):
		
		self.flight_time = self.overall_time

		if self.velocity > self.max_speed:
			self.max_speed = self.velocity

		if self.position[ZEROTH_ORDER][Z] > self.max_height:
			self.max_height = self.position[ZEROTH_ORDER][Z]

		for DOF in range(0,3):
			if abs(self.position[FIRST_ORDER][DOF]) > self.max_velocity:
				self.max_velocity = abs(self.position[FIRST_ORDER][DOF])
			if abs(self.position[SECOND_ORDER][DOF]) > self.max_acceleration_DOF:
				self.max_acceleration_DOF = abs(self.position[SECOND_ORDER][DOF])

		accel_result = sqrt(math.pow(self.position[SECOND_ORDER][X],2)+math.pow(self.position[SECOND_ORDER][Y],2)+math.pow(self.position[SECOND_ORDER][Z],2))
		if accel_result > self.max_acceleration_mag:
			self.max_acceleration_mag = accel_result

		self.distance_from_pad = sqrt(math.pow(self.position[ZEROTH_ORDER][X], 2) + math.pow(self.position[ZEROTH_ORDER][Y], 2))

	def update_state(self):

		self.update_metrics()

		#update 1 Dimension acceleration for forces in direction of the rocket
		self.accel = (-self.drag_const*self.velocity*self.velocity + self.thrust)/self.mass

		#add random angle noise here
		#propgate that through accel and vel to position

		#update 3DOF angle based on phi and theta at time t
		for order in range(0,1):
			self.angle[order][Z] = cos(self.phi[order])
			self.angle[order][X] = sin(self.phi[order])*cos(self.theta[order])
			self.angle[order][Y] = sin(self.phi[order])*sin(self.theta[order])

		#break acceleration magnitude into 3 DOF accel and add 3DOF forces/accelerations
		for DOF in range(0,3):
			self.position[SECOND_ORDER][DOF] = self.accel*self.angle[ZEROTH_ORDER][DOF]
			self.position[SECOND_ORDER][Z] -= self.model.gravity

		#Acceleration(t) and velocity(t) update position(t+1)
		#Acceleration(t) updates velocity(t+1)
		for DOF in range(0,3):
			self.position[ZEROTH_ORDER][DOF] += self.position[FIRST_ORDER][DOF]*self.model.time_step + 0.5*self.position[SECOND_ORDER][DOF]*self.model.time_step*self.model.time_step
			self.position[FIRST_ORDER][DOF] += self.position[SECOND_ORDER][DOF]*self.model.time_step

		#Get Velocity(t+1) magnitude
		self.velocity = sqrt(math.pow(self.position[FIRST_ORDER][X],2)+math.pow(self.position[FIRST_ORDER][Y],2)+math.pow(self.position[FIRST_ORDER][Z],2))

		#Update phi(t+1) and theta(t+1) based on velocity(t+1) resultant
		temp_theta = math.atan((self.position[FIRST_ORDER][Y]/(self.position[FIRST_ORDER][X]+0.0000001)))
		if (self.position[FIRST_ORDER][X] < 0):
			#Quadrant II and III
			temp_theta = PI + temp_theta
		if (self.position[FIRST_ORDER][X] >= 0):
			#Quadrant I and IV
			temp_theta = 2*PI + temp_theta
		self.theta[ZEROTH_ORDER] = temp_theta

		self.phi[ZEROTH_ORDER] = math.acos((self.position[FIRST_ORDER][Z]/(self.velocity+0.000001)))

		self.overall_time += self.model.time_step

		if self.print_each_step:
			self.time_step_print()
		
		time.sleep(self.model.time_step)

#======================= Global Variables and Objects =================
#Global Variables
vid_record_file = 'buffer_recording.h264' #on-board file video is stored to
bitrate_max = 200000 # bits per second
#record_time = 10.1 # Time in seconds that the recording runs for
record_chunk = 0.2 #chunk size in seconds video object is broken into and sent 
frame_rate = 15 #camera frame rate
interrupt_bool = False #global interrupt flag that ends recording/program
store_and_send_bool = False #global interrupt flag that initiates sending and storing of camera data

#ensures chunk size is not smaller than one frame
if record_chunk < 1/frame_rate:
	record_chunk = 1/frame_rate

telem_record_file = 'telemtry_stream.txt'

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
		vid_sock.connect_ex((SERVER_IP, SERVER_VIDEO_PORT))
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
		telem_sock.connect_ex((SERVER_IP, SERVER_TELEM_PORT))
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

print("Beginning Stream!")

#Begin Pi Cam recording
camera.start_recording(stream, format='h264', bitrate=bitrate_max)

vid_loop_sum = 0
vid_comms_sum = 0
vid_store_sum = 0
vid_max_packet = 0
vid_max_comms = 0

#Initiate Rocket Sim
test_rocket = rocket(9.8, 0, 0.05, 0.0)
test_rocket.transpose_rocket_frame_to_ground_frame()

#Start timer threads
#threading.Timer(record_time, interrupt_func).start()
threading.Timer(record_chunk, store_interrupt_func).start()

program_start = time.time()

#Main Program Loop
while test_rocket:
	if (test_rocket.overall_time < 2):
		test_rocket.thrust = 80.0
	else:
		test_rocket.thrust = 0.0
	test_rocket.update_state()

	packet_Bytes = test_rocket.form_bin_packet()
	if (packet_Bytes):
		print("========================= Telemetry ============================")
		packet_size = len(packet_Bytes)
		print("Current Packet | Size(%d):"%(packet_size))
		print(packet_Bytes)
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
print("\n\nClosing Connection")
vid_sock.close()
telem_sock.close()
print("Ending Recording")
camera.stop_recording()
print("Closing Record Files")
camera_file_handle.close()
telem_file_handle.close()
print("Program Time:  %fs"%(total_time))
print("Video Process Time:  %fs | Video Process Usage: %f%%"%(vid_loop_sum, (vid_loop_sum*100)/total_time))
print("\tComms: %fs | %f%%\n\tStore: %fs | %f%%"%(vid_comms_sum, (vid_comms_sum*100)/vid_loop_sum, vid_store_sum,(vid_store_sum*100)/vid_loop_sum))
print("\tStream Metrics:\n\t\tMax Packet Size: %d Bytes\n\t\tMax Send Time  : %f ms\n"%(vid_max_packet, vid_max_comms*1000))
test_rocket.print_flight_metrics()

