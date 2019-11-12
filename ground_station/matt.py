#Modified script. Change location.txt to add to graph

from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
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

SERVER_IP = ''
SERVER_VID_PORT = 5000
SERVER_TELEM_PORT = 5001


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

class stream:
	def __init__(self, name, server_socket, store_file):
		self.name = name
		self.server_socket = server_socket
		self.client_socket = None
		self.packet_cnt = 0
		self.total_bytes = 0
		self.store_file = store_file
		self.file_first_time = True
		self.file_handle = None #open(store_file, 'wb')
		self.data_point_buffer = []
		self.buffer = BytesIO()
		self.alive = True
	
	def __bool__(self):
		return self.alive

	def store_buffer(self):
		#print("%s: Storing Buffer"%(self.name))
		self.file_handle.write(self.buffer.getvalue())
		
	def get_buffer_size(self):
		return self.buffer.getbuffer().nbytes

	def clear_buffer(self):
		#print("%s: Clearing Buffer"%(self.name))
		self.buffer.truncate(0)
		self.buffer.seek(0)
	
	def close(self, selector_obj):
		self.store_buffer()
		self.clear_buffer()
		self.file_handle.close()
		self.alive = False
		selector_obj.unregister(self.client_socket)
		self.client_socket.close()
		self.client_socket = None

	def connect_src(self, selector_obj):
		if (self.client_socket is not None):
			print("Client Socket already connected! Rejecting connection")
			return
		self.client_socket, addr = self.server_socket.accept()
		print("%s Stream connected from (%s, %d)"%(self.name, addr[0], addr[1]))
		self.client_socket.setblocking(False)
		data = types.SimpleNamespace(addr=addr, inb=b'', outb = b'')
		events = selectors.EVENT_READ | selectors.EVENT_WRITE
		selector_obj.register(self.client_socket, events, data=data)
		if (self.file_first_time):
			self.file_handle = open(self.store_file, 'wb')
			self.file_first_time = False
		else:
			self.file_handle = open(self.store_file, 'ab')

		self.alive = True

	def recv_new_packet(self, selector_obj):
		packet = self.client_socket.recv(4096)
		if (not(packet)):
			print("%s: Stream ended. Closing Client Connection and Unregistering with selector"%(self.name))
			self.close(selector_obj)
			return
		print("%s: New Packet | Size: %d Bytes"%(self.name, len(packet)))
		self.buffer.write(packet)
		self.packet_cnt += 1
		self.total_bytes += len(packet)
		

def parse_telemetry(telem_packets, data_point_buffer):
	status_str = ['BAD', 'OK']
	code_word = bytearray([192,222]) #0xC0DE (Beginning of Packet)
	EOP = bytearray([237,12]) #0xED0C (End of Packet)
	packet_list = telem_packets.split(code_word)
	for packets in packet_list:
		good_packet = False
		try:
			data = struct.unpack('>ii???????ffffffffffh', packets)
			if packets[51:53] == EOP:
				good_packet = True
			else:
				print("End of Packet check failed")
				print("\tPacket End: %s"%(packets[51:53]))
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

server_vid_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_vid_sock.bind((SERVER_IP, SERVER_VID_PORT))
server_vid_sock.listen()
server_vid_sock.setblocking(False)
print("%s Server Created and Listening on (%s, %d)"%('VIDEO', server_vid_sock.getsockname()[0], server_vid_sock.getsockname()[1]))


server_telem_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_telem_sock.bind((SERVER_IP, SERVER_TELEM_PORT))
server_telem_sock.listen()
server_vid_sock.setblocking(False)
print("%s Server Created and Listening on (%s, %d)"%('VIDEO', server_telem_sock.getsockname()[0], server_telem_sock.getsockname()[1]))

sel = selectors.DefaultSelector()
sel.register(server_vid_sock, selectors.EVENT_READ, data=None)
sel.register(server_telem_sock, selectors.EVENT_READ, data=None)

video_file = store_dir + '/video_stream_recording.h264'
telem_file = store_dir + '/telemetry_stream.txt'


#Create Local UDP source for gstreamer
LOCAL_IP = '127.0.0.1'
LOCAL_PORT = 4000

local_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_addr = (LOCAL_IP, LOCAL_PORT)

#Create stream objects
video_stream = stream('VIDEO', server_vid_sock, video_file)
telem_stream = stream('TELEMETRY', server_telem_sock, telem_file)


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
	(ox,oy,oz) = (0,0,0)
	#data_point_buffer = []

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
				socket_obj = key.fileobj
				if (socket_obj == video_stream.server_socket):
					video_stream.connect_src(sel)

				if (socket_obj == telem_stream.server_socket):
					telem_stream.connect_src(sel)

			if key.data is not(None) and mask == selectors.EVENT_READ | selectors.EVENT_WRITE:
				socket_obj = key.fileobj
				if ((socket_obj == video_stream.server_socket or socket_obj == video_stream.client_socket) and video_stream):
					video_stream.recv_new_packet(sel)
					if video_stream.get_buffer_size() > 1000:
						#Buffer Reached Threshold

						#Process Buffer data
						local_sock.sendto(video_stream.buffer.getvalue(), recv_addr)

						#Store Buffer to file
						video_stream.store_buffer()

						#Clear Buffer
						video_stream.clear_buffer()

				if ((socket_obj == telem_stream.server_socket or socket_obj == telem_stream.client_socket) and telem_stream):
					telem_stream.recv_new_packet(sel)
					if telem_stream.get_buffer_size() > 500:
						#Buffer Reached Threshold

						#Process Buffer data
						telem_stream.data_point_buffer = parse_telemetry(telem_stream.buffer.getvalue(), telem_stream.data_point_buffer)

						#Store Buffer to file
						telem_stream.store_buffer()

						#Clear Buffer
						telem_stream.clear_buffer()

		if (len(telem_stream.data_point_buffer) > 0):
			for i in range(0,2):
				try:
					print("Popping Data point off and updating plot")
					new_point = telem_stream.data_point_buffer.pop(0)
				except:
					pass
			x, y, z = new_point.position[0], new_point.position[1], new_point.position[2] 
			if (x,y,z) != (self.ox,self.oy,self.oz):
				(self.ox, self.oy, self.oz) = (x,y,z)
				self.plot.update(x, y, z)
				self.tel.update(z, math.sqrt(y**2 + x**2), math.sqrt(new_point.velocity[0]**2 +new_point.velocity[1]**2+ new_point.velocity[2]**2  ))						
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
