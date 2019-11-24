#!/usr/bin/env python3
#!bin/bash
# /etc/init.d/telem_sim_and_video_stream.py
### BEGIN INIT INFO
# Provides:          telem_sim_and_video_stream.py
# Required-Start:    $all
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO


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
from pathlib import Path

home = str(Path.home())
print("Home Directory: %s"%(home))
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

#state variable 'macros'
ZEROTH_ORDER = 0
FIRST_ORDER = 1
SECOND_ORDER = 2

X = 0
Y = 1
Z = 2

#Constant Macros
PI = 3.1415926535
STREAM_READ = 1
STREAM_WRITE = 2

#======================= TRAJECTORY SIMULATION CODE =================
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
		self.drag_const  = 0.001 #0.5*Cd*A*p all lumped together | reasonable is around 0.01 or less

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
			#print("New Packet at time: %f | %d"%(self.overall_time, int(self.overall_time*100)%10))
			self.packet_cnt += 1
			packet_bytes = bytearray([192, 222]) #0xC0DE in hex (BEGINNING OF PACKET)
			packet_bytes += bytearray(struct.pack('>ii', self.packet_cnt, int(self.overall_time*100)))
			packet_bytes += bytearray(struct.pack('>???????', 1,0,1,1,0,1,1))
			packet_bytes += bytearray(struct.pack('>fff', self.position[0][0], self.position[0][1], self.position[0][2]))
			packet_bytes += bytearray(struct.pack('>fff', self.position[1][0], self.position[1][1], self.position[1][2]))
			packet_bytes += bytearray(struct.pack('>ffff', self.angle[0][0], self.angle[0][1], self.angle[0][2], 0.0))
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


#======================= Global Variables and Objects =================
#Global Variables
vid_record_file = store_dir + '/video_stream.h264' #on-board file video is stored to
telem_record_file = store_dir + '/telemtry_stream.txt'
bitrate_max = 100000 # bits per second
#record_time = 10.1 # Time in seconds that the recording runs for
record_chunk = 0.2 #chunk size in seconds video object is broken into and sent 
frame_rate = 15 #camera frame rate
interrupt_bool = False #global interrupt flag that ends recording/program
store_and_send_bool = False #global interrupt flag that initiates sending and storing of camera data

#ensures chunk size is not smaller than one frame
if record_chunk < 1/frame_rate:
	record_chunk = 1/frame_rate

#Camera Settings
camera = PiCamera()
camera.resolution = (640, 480)
#camera.resolution = (320, 240)
camera.framerate = frame_rate

#Network Setup
SERVER_IP = '73.136.139.198'
SERVER_IP = '10.0.0.223'
SERVER_VIDEO_PORT = 5000
SERVER_TELEM_PORT = 5001

video_stream = client_stream("VIDEO", SERVER_IP, SERVER_VIDEO_PORT, None, vid_record_file, STREAM_WRITE)
telem_stream = client_stream("TELEMETRY", SERVER_IP, SERVER_TELEM_PORT, None, telem_record_file, STREAM_WRITE)

video_stream.connect_to_server()
telem_stream.connect_to_server()

#======================== Video Streaming and Recording ============
loop_cnt = 0.0
cnt = 0

print("Beginning Stream!")

#Begin Pi Cam recording
camera.start_recording(video_stream.write_buffer, format='h264', bitrate=bitrate_max)

#Initiate Rocket Sim
test_rocket = rocket(9.8, 0, 0.05, 0)
test_rocket.transpose_rocket_frame_to_ground_frame()

#Start timer threads
#threading.Timer(record_time, interrupt_func).start()
threading.Timer(record_chunk, store_interrupt_func).start()

program_start = time.time()

#Main Program Loop
while test_rocket:
	if (test_rocket.overall_time < 3):
		test_rocket.thrust = 150.0
	else:
		test_rocket.thrust = 0.0
	test_rocket.update_state()

	packet_Bytes = test_rocket.form_bin_packet()
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

test_rocket.print_flight_metrics()

absolute_tm = time.localtime()
time_str = "\nScript Ended at " + str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5])
time_str += " on " + str(absolute_tm[1]) + "/" + str(absolute_tm[2]) + "/" + str(absolute_tm[0])

log_handle.write(time_str)

log_handle.close() 

