import socket
import selectors
from io import BytesIO
import types
import struct

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
		print("\tStatus:  %d   %d   %d    %d      %d    %d     %d"%(status[0], status[1], status[2], status[3], status[4], status[5], status[6]))
		print("\t             X       Y       Z")
		print("\tPosition:  %.2f    %.2f    %.2f"%(position[0], position[1], position[2]))
		print("\t             X       Y       Z")
		print("\tVelocity:  %.2f    %.2f    %.2f"%(velocity[0], velocity[1], velocity[2]))
		print("\t             X       Y       Z")
		print("\tOrientat:  %.2f    %.2f    %.2f"%(orientation[0], orientation[1], orientation[2]))

class stream:
	def __init__(self, name, server_socket, client_socket, store_file):
		self.name = name
		self.server_socket = server_socket
		self.client_socket = client_socket
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
			print("%s: Stream ended, closing connection and file"%(self.name))
			self.alive = False
			self.close()
			return
		print("%s: New Packet | Size: %d Bytes"%(self.name, len(packet)))
		self.buffer.write(packet)
		self.packet_cnt += 1
		self.total_bytes += len(packet)
		

def parse_telemetry(telem_packets, data_point_buffer):
	code_word = bytearray([192,222])
	EOP = bytearray([237,12])
	packet_list = telem_packets.split(code_word)
	for packets in packet_list:
		good_packet = False
		try:
			packet_num, time_stamp = struct.unpack('>ii',packets[0:8])
			imu, gps, alt, teensy, raspi, LTE, serial = struck.unpack('>???????', packets[8:15])
			posX, posY, posZ = struct.unpack('>fff', packets[15:27])
			velX, velY, velZ = struct.unpack('>fff', packets[27:39])
			roll, pitch, yaw = struct.unpack('>fff', packets[39:51])
			if packets[51:53] == EOP:
				good_packet = True
		except:
			print("Bad Packet!")
			pass
		if (good_packet):
			status_list = [imu, gps, alt, teensy, raspi, LTE, serial]
			pos_list = [posX, posY, posZ]
			vel_list = [velX, velY, velZ]
			orient_list = [roll, pitch, yaw]
			new_data = data_point(packet_num, time_stamp, status_list, pos_list, vel_list, orient_list)
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

video_file = 'video_stream_recording.h264'
telem_file = 'telemetry_stream.txt'


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
	events = sel.select(timeout=None)#BLOCKING, can set timeout to not block
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
				if telem_stream.get_buffer_size() > 2000:
					#Buffer Reached Threshold
	
					#Process Buffer data
					parse_telemetry(telem_stream.buffer.getvalue())

					#Store Buffer to file
					telem_stream.store_buffer()
					
					#Clear Buffer
					telem_stream.clear_buffer()

print("Stream Ended")
print("Stream Statistics: \n\tVIDEO Bytes: %d\n\tTELEM Bytes: %d"%(video_stream.total_bytes, telem_stream.total_bytes))




