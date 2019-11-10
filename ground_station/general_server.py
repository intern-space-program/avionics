import socket
import selectors
from io import BytesIO
import types
import struct
from pathlib import Path
import os

home = str(Path.home())
print("Home Directory: %s"%(home))
store_dir = home + "/rocket_data"
cmd = "mkdir " + store_dir
os.system(cmd)

SERVER_IP = ''
SERVER_VID_PORT = 5000
SERVER_TELEM_PORT = 5001

video_ports = [SERVER_VID_PORT]
telem_ports = [SERVER_TELEM_PORT]

def name_source(socket_obj):
	port = socket_obj.getsockname()[1]
	named = False
	for ports in video_ports:
		if port == ports:
			named = True
			return 'VIDEO'
	for ports in telem_ports:
		if port == ports:
			named = True
			return 'TELEMETRY'
	if (not(named)):
		return False

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
		print("\t        IMU  GPS  ALT  Teensy  Raspi  LTE  Serial")
		print("\tStatus:  %d   %d    %d      %d        %d       %d        %d"%(self.status[0], self.status[1], self.status[2], self.status[3], self.status[4], self.status[5], self.status[6]))
		print("\t             X       Y       Z")
		print("\tPosition:  %.2f    %.2f    %.2f"%(self.position[0], self.position[1], self.position[2]))
		print("\t             X       Y       Z")
		print("\tVelocity:  %.2f    %.2f    %.2f"%(self.velocity[0], self.velocity[1], self.velocity[2]))
		print("\t             X       Y       Z")
		print("\tOrientat:  %.2f    %.2f    %.2f"%(self.orientation[0], self.orientation[1], self.orientation[2]))

class stream:
	def __init__(self, name, server_socket, client_socket, store_file):
		self.name = name
		self.server_socket = server_socket
		self.source_sockets = []
		self.sink_sockets = []
		self.packet_cnt = 0
		self.total_bytes = 0
		self.store_file = store_file
		self.file_handle = open(store_file, 'wb')
		self.buffer = BytesIO()
		self.alive = True
	
	def __bool__(self):
		return self.alive

	def store_buffer(self):
		print("%s: Storing Buffer"%(self.name))
		self.file_handle.write(self.buffer.getvalue())
		
	def get_buffer_size(self):
		return self.buffer.getbuffer().nbytes

	def clear_buffer(self):
		print("%s: Clearing Buffer"%(self.name))
		self.buffer.truncate(0)
		self.buffer.seek(0)
	
	def close(self):
		self.store_buffer()
		self.clear_buffer()
		self.file_handle.close()
		self.server_socket.close()

	def recv_new_packet(self):
		packet = self.client_socket.recv(4096)
		if (not(packet)):
			print("%s: Stream ended, storing, then closing connection and file"%(self.name))
			self.alive = False
			self.close()
			return
		print("%s: New Packet | Size: %d Bytes"%(self.name, len(packet)))
		self.buffer.write(packet)
		self.packet_cnt += 1
		self.total_bytes += len(packet)
		

def parse_telemetry(telem_packets, data_point_buffer):
	code_word = bytearray([192,222]) #0xC0DE (Beginning of Packet)
	EOP = bytearray([237,12]) #0xED0C (End of Packet)
	packet_list = telem_packets.split(code_word)
	for packets in packet_list:
		good_packet = False
		try:
			data = struct.unpack('>ii???????fffffffffh', packets)
			if packets[51:53] == EOP:
				good_packet = True
			else:
				print("End of Packet check failed")
				print("\tPacket End: %s"%(packets[51:53]))
				print("\tEOP:        %s"%(EOP))
		except:
			print("BAD PACKET")

		if (good_packet):
			status_list = [data[2], data[3], data[4], data[5], data[6], data[7], data[8]]
			pos_list = [data[9], data[10], data[11]]
			vel_list = [data[12], data[13], data[14]]
			orient_list = [data[15], data[16], data[17]]
			new_data = data_point(data[0], data[1], status_list, pos_list, vel_list, orient_list)
			new_data.print_data_point()
			data_point_buffer.append(new_data)
	
	return data_point_buffer


server_vid_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_vid_sock.bind((SERVER_IP, SERVER_VID_PORT))
server_vid_sock.listen()
print("%s Server Created and Listening on (%s, %d)"%(name_source(server_vid_sock), server_vid_sock.getsockname()[0], server_vid_sock.getsockname()[1]))


server_telem_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_telem_sock.bind((SERVER_IP, SERVER_TELEM_PORT))
server_telem_sock.listen()
print("%s Server Created and Listening on (%s, %d)"%(name_source(server_telem_sock), server_telem_sock.getsockname()[0], server_telem_sock.getsockname()[1]))

sel = selectors.DefaultSelector()
sel.register(server_vid_sock, selectors.EVENT_READ, data=None)
sel.register(server_telem_sock, selectors.EVENT_READ, data=None)

video_file = store_dir + '/video_stream_recording.h264'
telem_file = store_dir + '/telemetry_stream.txt'


#Wait for Video connection (First one to Initiate)
vid_client, addr = server_vid_sock.accept()
print("VIDEO Stream connected from (%s, %d)"%(addr[0], addr[1]))
vid_client.setblocking(False)
video_ports.append(addr[1])
data = types.SimpleNamespace(addr=addr, inb=b'', outb = b'')
events = selectors.EVENT_READ | selectors.EVENT_WRITE
sel.register(vid_client,events, data=data)


#Wait for Telemetry connection(Second one to Initiate)
telem_client, addr = server_telem_sock.accept()
print("TELEMETRY Stream connected from (%s, %d)"%(addr[0], addr[1]))
telem_client.setblocking(False)
telem_ports.append(addr[1])
data = types.SimpleNamespace(addr=addr, inb=b'', outb = b'')
events = selectors.EVENT_READ | selectors.EVENT_WRITE
sel.register(telem_client, events, data=data)

#Now that connection order doesn't matter, set blocking to false
server_vid_sock.setblocking(False)
server_telem_sock.setblocking(False)

#Create stream objects
video_stream = stream('VIDEO', server_vid_sock, vid_client, video_file)
telem_stream = stream('TELEMETRY', server_telem_sock, telem_client, telem_file)

data_point_buffer = []

while video_stream or telem_stream:
	events = sel.select(timeout=0.1)#BLOCKING, can set timeout to not block
	for key, mask in events:
		if key.data is None:
			print("CONNECTION ATTEMPT")
		if key.data is not(None) and mask == selectors.EVENT_READ | selectors.EVENT_WRITE:
			socket_obj = key.fileobj
			if (name_source(socket_obj) == 'VIDEO' and video_stream):
				video_stream.recv_new_packet()
				if video_stream.get_buffer_size() > 10000:
					#Buffer Reached Threshold
	
					#Process Buffer data
		
					#Store Buffer to file
					video_stream.store_buffer()
					
					#Clear Buffer
					video_stream.clear_buffer()

			if (name_source(socket_obj) == 'TELEMETRY' and telem_stream):
				telem_stream.recv_new_packet()
				if telem_stream.get_buffer_size() > 500:
					#Buffer Reached Threshold
	
					#Process Buffer data
					data_point_buffer = parse_telemetry(telem_stream.buffer.getvalue(), data_point_buffer)

					#Store Buffer to file
					telem_stream.store_buffer()
					
					#Clear Buffer
					telem_stream.clear_buffer()

print("Stream Ended")
print("Stream Statistics: \n\tVIDEO Bytes: %d\n\tTELEM Bytes: %d"%(video_stream.total_bytes, telem_stream.total_bytes))




