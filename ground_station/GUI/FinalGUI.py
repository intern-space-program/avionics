#Modified script. Change location.txt to add to graph

from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  
from kivy.uix.label import Label
from kivy.clock import Clock
import random
import matplotlib.animation as animation
from matplotlib import use as mpl_use
import socket
import selectors
from io import BytesIO
import types
import struct
from pathlib import Path
import os
import math

home = str(Path.home())
print("Home Directory: %s"%(home))
store_dir = home + "/rocket_data"
cmd = "mkdir " + store_dir
os.system(cmd)


class data_point:
	def __init__(self, packet_num, time_stamp, status_list, pos_list, vel_list, orientation_list):
		self.packet_num = packet_num
		self.time_stamp = time_stamp
		self.status = status_list #[imu, gps, alt, teensy, raspi, LTE, serial]
		self.position = pos_list #[X, Y, Z]
		self.velocity = vel_list #[X, Y, Z]
		self.orientation = orientation_list #[Roll, Pitch, Yaw]
	
	def print_data_point(self):
		print("Data Point:")
		print("\tPacket Number: %d"%(self.packet_num))
		print("\tTime Stamp: %d"%(self.time_stamp))
		print("\t		IMU  GPS  ALT  Teensy  Raspi  LTE  Serial")
		print("\tStatus:  %s   %s	%s	  %s		%s	   %s		%s"%(self.status[0], self.status[1], self.status[2], self.status[3], self.status[4], self.status[5], self.status[6]))
		print("\t			 X	   Y	   Z")
		print("\tPosition:  %.2f	%.2f	%.2f"%(self.position[0], self.position[1], self.position[2]))
		print("\t			 X	   Y	   Z")
		print("\tVelocity:  %.2f	%.2f	%.2f"%(self.velocity[0], self.velocity[1], self.velocity[2]))
		print("\t			 X	   Y	   Z")
		print("\tOrientat:  %.2f	%.2f	%.2f"%(self.orientation[0], self.orientation[1], self.orientation[2]))

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
		self.data_point_buffer = []
		self.alive = False
		self.read_file = False
		self.write_file = False
		self.print_output = True
		self.log_output = False
		self.kill_cnt = 0
		
		if (mode & STREAM_READ == STREAM_READ):
			self.read_buffer = BytesIO()
			try:  
				self.read_file_handle = open(read_store_file, 'wb')
				self.read_file = True
			except:
				self.read_file = False

		if (mode & STREAM_WRITE == STREAM_WRITE):
			self.write_buffer = BytesIO()
			try: 
				self.write_file_handle = open(write_store_file, 'wb')
				self.write_file = True
			except:
				self.write_file = False

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
	
	def register_with_server(self, selector_obj):
		if not(self.alive):
			return
		self.stream_print("Registering with server")
		self.log_print("Registering with server")
		self.send_packet(b'sink', selector_obj)

	def start_stream(self, selector_obj):
		if (self.name == 'TELEMETRY' and self.alive):
			self.send_packet(b'I wanna turn you on daddy', selector_obj)

	def kill_stream(self, selector_obj):
		if (self.name == 'TELEMETRY' and self.alive):
			if self.kill_cnt < 4:
				self.kill_cnt += 1
			else:
				self.send_packet(b'KILL STREAM', selector_obj)


	def connect_to_server(self, selector_obj):
		connect_cnt = 0
		self.log_print("Attempting to connect to server")
		while connect_cnt < 5:
			self.stream_print("Server connection attempt #%d"%(connect_cnt+1))
			try:
				self.socket_obj.connect_ex((self.server_IP, self.server_port))
				self.stream_print("Connection Successful")
				self.log_print("Connection Successful")
				self.alive = True
				events = selectors.EVENT_READ|selectors.EVENT_WRITE
				selector_obj.register(self.socket_obj, events, data=self.name)
				break
			except:
				connect_cnt += 1

		self.register_with_server(selector_obj)
	
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
	
	def close(self, selector_obj):
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
				self.send_packet(self.write_buffer.getvalue(), selector_obj)
			self.store_buffer(STREAM_WRITE)
			self.clear_buffer(STREAM_WRITE)
			self.close_file(STREAM_WRITE)

		self.close_socket(selector_obj)
	
	def close_socket(self, selector_obj):
		if (not(self.alive)):
			return
		self.alive = False
		self.stream_print("Closing Socket")
		selector_obj.unregister(self.socket_obj)
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
	
	def send_packet(self, msg, selector_obj):
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
				self.close_socket(selector_obj)
				
		
	def recv_new_packet(self, selector_obj):
		if (not(self.alive)):
			return None
		if (not(self.mode & STREAM_READ)):
			self.stream_print("READ ACCESS DENIED")
		else:
			packet = self.socket_obj.recv(4096)
			if (not(packet)):
				self.stream_print("Stream ended, storing, then closing connection and file")
				self.log_print("Stream ended, storing, then closing connection and file")
				self.close_socket(selector_obj)
				return None
			search = "KILL STREAM"
			if packet.find(search.encode('utf-8')) != -1:
				self.stream_print("KILL statement heard, doing full close")
				self.log_print("KILL statement heard, doing full close")
				self.close(selector_obj)
				return "kill"
			self.stream_print("%s: New Packet | Size: %d Bytes"%(self.name, len(packet)))
			if self.name == 'TELEMETRY':
				self.stream_print(packet)
			self.read_buffer.write(packet)
			self.recv_packet_cnt += 1
			self.recv_total_bytes += len(packet)
			return None
		
#========================= FUNCTIONS ============================
def parse_telemetry(telem_packets, data_point_buffer):
	status_str = ['BAD', 'OK']
	code_word = bytearray([192,222]) #0xC0DE (Beginning of Packet)
	EOP = bytearray([237,12]) #0xED0C (End of Packet)
	packet_list = telem_packets.split(code_word)
	for packets in packet_list:
		good_packet = False
		try:
			data = struct.unpack('>ii???????ffffffffffh', packets)
			if packets[55:57] == EOP:
				good_packet = True
			else:
				print("End of Packet check failed")
				print("\tPacket End: %s"%(packets[55:57]))
				print("\tEOP:		%s"%(EOP))
		except:
			print("BAD PACKET")

		if (good_packet):
			status_list = [status_str[data[2]], status_str[data[3]], status_str[data[4]], status_str[data[5]], status_str[data[6]], status_str[data[7]], status_str[data[8]]]
			pos_list = [data[9], data[10], data[11]]
			vel_list = [data[12], data[13], data[14]]
			orient_list = [data[15], data[16], data[17], data[18]]
			new_data = data_point(data[0], data[1], status_list, pos_list, vel_list, orient_list)
			#new_data.print_data_point()
			data_point_buffer.append(new_data)

	return data_point_buffer

sel = selectors.DefaultSelector()

video_file = store_dir + '/video_stream_recording.h264'
telem_file = store_dir + '/telemetry_stream.txt'
cmd_file = store_dir + '/telem_commands.txt'


#Create Local UDP source for gstreamer
LOCAL_IP = '127.0.0.1'
LOCAL_PORT = 4000

local_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_addr = (LOCAL_IP, LOCAL_PORT)

#Create stream objects
SERVER_IP = '73.115.48.151'
SERVER_VID_PORT = 5000
SERVER_TELEM_PORT = 5001
#def __init__(self, name, server_IP, server_port, read_store_file, write_store_file, mode):
video_stream = client_stream('VIDEO', SERVER_IP, SERVER_VID_PORT, video_file, None, STREAM_READ|STREAM_WRITE)
telem_stream = client_stream('TELEMETRY', SERVER_IP, SERVER_TELEM_PORT, telem_file, cmd_file, STREAM_READ|STREAM_WRITE)

video_stream.connect_to_server(sel)
telem_stream.connect_to_server(sel)

mpl_use('module://kivy.garden.matplotlib.backend_kivy')

class Video(Label):
	pass

class Telemetry(GridLayout):
	def update(self, alt, dist, vel):
		self.ids.alt.text = '%.2f'%alt
		self.ids.pos.text = '%.2f'%dist  
		self.ids.vel.text = '%.2f'%vel
	pass

class Status(GridLayout):
	def clearPlot(instance):
		instance.parent.clearPlot()
	
	def killStream(instance, button):
		instance.parent.clicks_rem -= 1
		button.text = "Kill Stream\n(" + '%d'%instance.parent.clicks_rem + " clicks remaining)"
		if (instance.parent.clicks_rem < 1) :
			button.text = "Matt sends\nhis regards"
		
		telem_stream.kill_stream(sel)
		
		
	def startStream(instance):
		telem_stream.start_stream(sel)

	def update(self, fIMU, fGPS, fALT, fTeensy, fRaspi, fLTE, fSerial):
		self.ids.IMU.text = fIMU
		self.ids.GPS.text = fGPS
		self.ids.ALT.text = fALT
		self.ids.Teensy.text = fTeensy
		self.ids.Raspi.text = fRaspi
		self.ids.LTE.text = fLTE
		self.ids.Serial.text = fSerial
		self.ids.IMU.color = (0,1,0,1) if fIMU == 'OK' else (1,0,0,1) 
		self.ids.GPS.color = (0,1,0,1) if fGPS == 'OK' else (1,0,0,1) 
		self.ids.ALT.color = (0,1,0,1) if fALT == 'OK' else (1,0,0,1) 
		self.ids.Teensy.color = (0,1,0,1) if fTeensy == 'OK' else (1,0,0,1) 
		self.ids.Raspi.color = (0,1,0,1) if fRaspi == 'OK' else (1,0,0,1) 
		self.ids.LTE.color = (0,1,0,1) if fLTE == 'OK' else (1,0,0,1) 
		self.ids.Serial.color = (0,1,0,1) if fSerial == 'OK' else (1,0,0,1) 
	pass

class Scran(FloatLayout):
	pass
class Seperator(FloatLayout):
	pass

class Plot(GridLayout): 
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	def addPlot(self):
		self.add_widget(self.fig.canvas)
		return self

	def update(self, x, y, z):
		self.ax.scatter(float(x),float(y),float(z), 'o', color='red')
		self.fig.canvas.draw_idle()
	pass

class MyGrid(GridLayout):
	tel = None
	plot = None
	stat = None
	clicks_rem = 5

	#data_point_buffer = []
	def clearPlot(self):
		self.plot.ax.clear()
		self.plot.fig.canvas.draw_idle()
		print("clear")
	def build(self):
		self.tel = Telemetry()
		self.plot = Plot(cols = 1)
		self.stat = Status()

		self.add_widget(Video())
		self.add_widget(self.plot.addPlot())
		self.add_widget(self.tel)
		self.add_widget(self.stat)
		return self
	def update(self,i):
		#BLOCKING, can set timeout to not block
		events = sel.select(timeout = 0.1)
		for key, mask in events:
			if key.data is None:
				print("CONNECTION ATTEMPT")

			if key.data is not(None) and mask == selectors.EVENT_READ|selectors.EVENT_WRITE:
				socket_obj = key.fileobj
				if (key.data == video_stream.name and video_stream):
					video_stream.recv_new_packet(sel)
					if video_stream.get_buffer_size(STREAM_READ) > 1000:
						#Buffer Reached Threshold

						#Process Buffer data
						local_sock.sendto(video_stream.read_buffer.getvalue(), recv_addr)

						#Store Buffer to file
						video_stream.store_buffer(STREAM_READ)

						#Clear Buffer
						video_stream.clear_buffer(STREAM_READ)

				if (key.data == telem_stream.name and telem_stream):
					telem_stream.recv_new_packet(sel)
					if telem_stream.get_buffer_size(STREAM_READ) > 500:
						#Buffer Reached Threshold

						#Process Buffer data
						telem_stream.data_point_buffer = parse_telemetry(telem_stream.read_buffer.getvalue(), telem_stream.data_point_buffer)

						#Storwe Buffer to file
						telem_stream.store_buffer(STREAM_READ)

						#Clear Buffer
						telem_stream.clear_buffer(STREAM_READ)

		if (len(telem_stream.data_point_buffer) > 0):
			for i in range(0,2):
				try:
					print("Popping Data point off and updating plot")
					new_point = telem_stream.data_point_buffer.pop(0)
				except:
					pass
			x, y, z = new_point.position[0], new_point.position[1], new_point.position[2]
			self.plot.update(x, y, z)
			self.tel.update(z, math.sqrt(y**2 + x**2), math.sqrt((new_point.velocity[0])**2 +(new_point.velocity[1])**2+ (new_point.velocity[2])**2  ))						
			self.stat.update(new_point.status[0], new_point.status[1], new_point.status[2], new_point.status[3], new_point.status[4], new_point.status[5], new_point.status[6])

class MattApp(App):
	grid = None
	def build(self):
		main = Scran()
		self.grid = MyGrid(cols = 2, size = (main.height, main.width), id  = 'grid')
		main.add_widget(self.grid.build())
		main.add_widget(Seperator())
		return main
	def on_start(self):
		Clock.schedule_interval(self.grid.update, .2)
		#code here?

MattApp().run()
#wont go here
