import socket
import selectors
from io import BytesIO
import types
import struct
import os
import time
import subprocess
import smtplib
from email.mime.text import MIMEText
from threading import Thread, Lock

home = '/home/ronnie' #TODO EDIT THIS BEFORE RUNNING TO REFLECT CURRENT HOME DIR
store_dir = home + "/rocket_data"
cmd = "mkdir " + store_dir
os.system(cmd)

SERVER_IP = ''
SERVER_VID_PORT = 5000
SERVER_TELEM_PORT = 5001

SRC2SINK = 1
SINK2SRC = 2
DUPLEX = SRC2SINK|SINK2SRC

send_email = True
#=================================  Send email with Global IP Address on start-up ===========================
# Account Information
gmail_file = home + "/gmail_info.txt"
try:
	gmail_info = open(gmail_file, 'r')
except:
	print("No gmail info file found. Disabling Email functionality")
	send_email = False
if send_email:
	to = 'ronnieankner@gmail.com' # Email to send to
	info = gmail_info.read()
	gmail_user = info.split('\n')[0] # Email to send from (MUST BE GMAIL)
	gmail_password = info.split('\n')[1] # 16-digit Google App Password if using 2-Step Verification

	def open_smtpserver():
		smtpserver = smtplib.SMTP('smtp.gmail.com', 587) # Server to use

		smtpserver.ehlo()  # Says 'hello' to the server
		smtpserver.starttls()  # Start TLS encryption
		smtpserver.ehlo()
		smtpserver.login(gmail_user, gmail_password)  # Log in to server

		return smtpserver

	ipaddr_a = subprocess.Popen(['curl', 'ifconfig.me'], stdout=subprocess.PIPE).communicate()[0]
	ipaddr_a = ipaddr_a.decode('utf-8')

	my_ip_a = 'Rocket Server Global IP address is %s' %(ipaddr_a)

	msg = MIMEText(my_ip_a)

	msg['Subject'] = 'Initial Global IP for Rocket Server'
	msg['From'] = gmail_user
	msg['To'] = to
	# Sends the message
	smtpServer = open_smtpserver()
	try:
		smtpServer.sendmail(gmail_user, [to], msg.as_string())
	except:
		print("Information in gmail file invalid!! Disabling Email Functionality")
		send_email = False
	smtpServer.quit()
#===========================================================================================================

THREAD_LOCK = Lock()

absolute_tm = time.localtime()
date_str = str(absolute_tm[1]) + "/" + str(absolute_tm[2]) + "/" + str(absolute_tm[0])

def get_time():
	absolute_tm = time.localtime()
	ms = time.time()
	ms = ms - int(ms)
	return str(absolute_tm[3]) + ":" + str(absolute_tm[4]) + ":" + str(absolute_tm[5]) + ":%.3f "%(ms)

class server_stream:
	def __init__(self, name, server_IP, server_port, selector_obj, src2sink_file, sink2src_file, mode, buffer_thresh):
		self.name = name
		self.server_IP = server_IP
		self.server_port = server_port
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		#List of socket objects in different registration bins
		self.undeclared_sockets = []
		self.sink_sockets = []
		self.src_sockets = []
		self.usernames = [] #dictionary where socket_obj is key, and name/position is 
		#TODO Functions: 
		#	1.collect usernames 
		#	2. update usernames 
		#	3. send list on request
		#TODO Functionality: 
		#	1.enforce name submission before allowed to register 
		#	2. add objects to Dict when connect 
		#	3. Remove from dict when leave 4. Notify all users when one has left
		
		self.src2sink_file = src2sink_file
		self.sink2src_file = sink2src_file
		self.mode = mode #can be SRC2SINK, SINK2SRC, or DUPLEX (SRC2SINK|SINK2SRC)
		self.buffer_thresh = buffer_thresh
		self.server_kill_requestor = None
		self.kill_request_time = None
		self.print_output = True #Controls Formatted output to the screen
		self.log_output = True #controls formatted output to overall system log file
		
		if (mode & SRC2SINK == SRC2SINK):
			self.src2sink_buffer = []
			if self.src2sink_file is not None:
				#Create new file if it does not exist, or overwrite old file if does
				self.src2sink_file_handle = open(self.src2sink_file, 'wb')
				self.src2sink_file_handle.write(b'Starting New Data log at '+get_time().encode('utf-8')+b' on '+date_str.encode('utf-8'))
				self.src2sink_file_handle.close() #close becuase future writes will be in append mode

		if (mode & SINK2SRC == SINK2SRC):
			self.sink2src_buffer = []
			if self.sink2src_file is not None:
				self.sink2src_file_handle = open(self.sink2src_file, 'wb')
				self.sink2src_file_handle.write(b'Starting New Data log at '+get_time().encode('utf-8')+b' on '+date_str.encode('utf-8'))
				self.sink2src_file_handle.close()
		
		self.server_socket.bind((self.server_IP, self.server_port))
		self.server_socket.listen()
		self.server_socket.setblocking(False)
		selector_obj.register(self.server_socket, selectors.EVENT_READ, data=None)
		print("%s: Server and stream created"%(self.name))
		self.alive = True
		
		#Statistics [OPTIONAL]
		self.recv_packet_cnt = 0
		self.recv_total_bytes = 0
		self.recv_time = 0.0

		self.send_packet_cnt = 0
		self.send_total_bytes = 0
		self.send_time = 0.0
		
	
	def __bool__(self):
		return self.alive
	
	def print_statistics(self):
		mode_name = ['SRC2SINK', 'SINK2SRC', 'SRC2SINK|SINK2SRC']
		#print("Stream Name: %s"%(self.name))
		#print("Stream Mode: %s"%(mode_name[self.mode-1]))
		#print("Read:\n\tPackets:     %d\n\tTotal Bytes: %d"%(self.recv_packet_cnt, self.recv_total_bytes))
		#print("Write:\n\tPackets:     %d\n\tTotal Bytes: %d"%(self.send_packet_cnt, self.send_total_bytes))

	def stream_print(self, msg):
		if (not(self.print_output)):
			return
		print("%s: %s"%(self.name, msg))

	def log_print(self, msg):
		if (not(self.log_output)):
			return
		log_start("%s: %s"%(self.name, msg))

	def print_socket(self, socket):
		try:
			return " (%s, %d)"%(socket.getpeername()[0], socket.getpeername()[1])
		except:
			self.stream_print("CANNOT RESOLVE PEER")
			return ""
	
	def print_state(self):
		if (not(self.print_output)):
			return
		state = ["DEAD", "ALIVE"]
		self.stream_print("Server State: %s"%(state[int(self.alive)]))
		print("\tUndeclared Sockets: %d"%(len(self.undeclared_sockets)))
		cnt = 0
		for sockets in self.undeclared_sockets:
			cnt += 1
			print("\t\t%d:"%(cnt), self.print_socket(sockets))
		print("\tSINK Sockets:       %d"%(len(self.sink_sockets)))
		cnt = 0
		for sockets in self.sink_sockets:
			cnt += 1
			print("\t\t%d:"%(cnt), self.print_socket(sockets))
		print("\tSRC Sockets:        %d"%(len(self.src_sockets)))
		cnt = 0
		for sockets in self.src_sockets:
			cnt += 1
			print("\t\t%d:"%(cnt), self.print_socket(sockets))
	
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

	def claim_socket(self, socket_obj):
		for socket in self.undeclared_sockets:
			if socket_obj == socket:
				return True
		for socket in self.sink_sockets:
			if socket_obj == socket:
				return True
		for socket in self.src_sockets:
			if socket_obj == socket:
				return True
		return False
	
	def handle_connection(self, selector_obj):
		client_sock, addr = self.server_socket.accept()
		self.stream_print("UNDECLARED Stream connected from (%s, %d)"%(addr[0], addr[1]))
		client_sock.setblocking(False)
		self.undeclared_sockets.append(client_sock)
		data = self.server_socket #make the client events identifiable by its server socket
		events = selectors.EVENT_READ | selectors.EVENT_WRITE
		selector_obj.register(client_sock, events, data=data)
		client_sock.sendall(b'Please register as "sink" or "src"')
		self.print_state()

	def pull_sample(self, mode):
		if (mode & SRC2SINK == SRC2SINK):
			if (not(self.mode & SRC2SINK)):
				self.stream_print("SRC2SINK ACCESS DENIED")
				return None
			if (len(self.src2sink_buffer) == 0):
				return None
			self.stream_print("Popping Sample off of SRC2SINK Buffer")
			return self.src2sink_buffer.pop(0)

		if (mode & SINK2SRC == SINK2SRC):
			if (not(self.mode & SINK2SRC)):
				self.stream_print("SINK2SRC ACCESS DENIED")
				return
			if (len(self.sink2src_buffer) == 0):
				return None
			self.stream_print("Popping Sample off of SINK2SRC Buffer")
			return self.sink2src_buffer.pop(0)
	
	def write_to_file(self, packet, mode):
		if (mode & SRC2SINK == SRC2SINK):
			if (not(self.mode & SRC2SINK)):
				self.stream_print("SRC2SINK ACCESS DENIED")
				return
			self.stream_print("Storing packet to SRC2SINK file")
			with open(self.src2sink_file, 'ab') as file_handle:
				file_handle.write(packet)

		if (mode & SINK2SRC == SINK2SRC):
			if (not(self.mode & SINK2SRC)):
				self.stream_print("SINK2SRC ACCESS DENIED")
				return
			self.stream_print("Storing packet to SINK2SRC file")
			with open(self.sink2src_file, 'ab') as file_handle:
				file_handle.write(packet)

	def store_buffer(self, mode):
		if (mode & SRC2SINK == SRC2SINK):
			if (not(self.mode & SRC2SINK)):
				self.stream_print("SRC2SINK ACCESS DENIED")
				return
			self.stream_print("Storing SRC2SINK Buffer")
			with open(self.src2sink_file, 'ab') as file_handle:
				while len(self.src2sink_buffer) > 0:
					packet = self.src2sink_buffer.pop(0)
					file_handle.write(packet)

		if (mode & SINK2SRC == SINK2SRC):
			if (not(self.mode & SINK2SRC)):
				self.stream_print("SINK2SRC ACCESS DENIED")
				return
			self.stream_print("Storing SINK2SRC Buffer")
			with open(self.sink2src_file, 'ab') as file_handle:
				while len(self.sink2src_buffer) > 0:
					packet = self.sink2src_buffer.pop(0)
					file_handle.write(packet)
		
	def get_buffer_size(self, mode):
		if (mode & SRC2SINK == SRC2SINK):
			if (not(self.mode & SRC2SINK)):
				self.stream_print("NO DOWNSTREAM BUFFER")
				return 0
			return len(self.src2sink_buffer)

		if (mode & SINK2SRC == SINK2SRC):
			if (not(self.mode & SINK2SRC)):
				self.stream_print("NO UPSTREAM BUFFER")
				return 0
			return len(self.sink2src_buffer)

	def clear_buffer(self, mode):
		if (mode & SRC2SINK == SRC2SINK):
			if (not(self.mode & SRC2SINK)):
				self.stream_print("NO SRC2SINK BUFFER")
				return
			if (len(self.src2sink_buffer) == 0):
				return
			self.stream_print("Clearing SRC2SINK Buffer")
			while len(self.src2sink_buffer) > 0:
				self.src2sink_buffer.pop(0)

		if (mode & SINK2SRC == SINK2SRC):
			if (not(self.mode & SINK2SRC)):
				self.stream_print("NO SINK2SRC BUFFER")
				return
			if (len(self.sink2src_buffer) == 0):
				return
			self.stream_print("Clearing SINK2SRC Buffer")
			while len(self.sink2src_buffer) > 0:
				self.sink2src_buffer.pop(0)
	
	def add_to_buffer(self, msg, mode):
		if (mode & SRC2SINK == SRC2SINK):
			if (not(self.mode & SRC2SINK)):
				self.stream_print("NO SRC2SINK BUFFER")
				return
			self.stream_print("Adding to SRC2SINK Buffer")
			self.src2sink_buffer.append(msg)

		if (mode & SINK2SRC == SINK2SRC):
			if (not(self.mode & SINK2SRC)):
				self.stream_print("NO SINK2SRC BUFFER")
				return
			self.stream_print("Adding to SINK2SRC Buffer")
			self.sink2src_buffer.append(msg)
	
	def close(self):
		self.stream_print("RUNNING FULL CLOSE")
		self.stream_print("Closing Server Socket")
		self.server_socket.close()
		self.alive = False
		self.print_state()
	
	def close_socket(self, socket_obj, selector_obj):
		if socket_obj in self.undeclared_sockets:
			self.undeclared_sockets.remove(socket_obj)
			selector_obj.unregister(socket_obj)
			socket_obj.close()
			return
		elif socket_obj in self.sink_sockets:
			self.sink_sockets.remove(socket_obj)
			selector_obj.unregister(socket_obj)
			socket_obj.close()
			return
		elif socket_obj in self.src_sockets:
			self.src_sockets.remove(socket_obj)
			selector_obj.unregister(socket_obj)
			socket_obj.close()
			return
		else:
			self.stream_print("ERROR SOCKET TO REMOVE NOT FOUND!!! Nothing to do")
			return
	
	def send_packet(self, msg, direction, selector_obj):
		if (direction & SRC2SINK == SRC2SINK):
			if (not(self.mode & SRC2SINK)):
				self.stream_print("NO SRC2SINK ACCESS")
				return
			self.stream_print("Sending Packet from SRC(s) -> SINK(s)")
			for socket in self.sink_sockets:
				try: 
					socket.sendall(msg)
				except:
					#Broken Pipe error; Socket no longer connected
					self.close_socket(socket, selector_obj)

		if (direction & SINK2SRC == SINK2SRC):
			if (not(self.mode & SINK2SRC)):
				self.stream_print("NO SINK2SRC ACCESS")
				return
			self.stream_print("Sending Packet from SINK(s) -> SRC(s)")
			for socket in self.src_sockets:
				try: 
					socket.sendall(msg)
				except:
					#Broken Pipe error; Socket no longer connected
					self.close_socket(socket, selector_obj)
	

	def kill_network(self, selector_obj):
		#kill switch for whole network -> ends Server [OPTIONAL] and all clients
		self.stream_print("KILL SWITCH RECIEVED. NOTIFYING ALL SINKS AND SOURCES")
		msg = b'KILL STREAM'
		self.stream_print("\tNotifiying %d UNDECLARED sockets and removing"%(len(self.undeclared_sockets)))
		while (len(self.undeclared_sockets) > 0):
			socket = self.undeclared_sockets[0]

			try: 
				socket.sendall(msg)
			except:
				self.stream_print("ERROR NOTIFYING" + self.print_socket(socket) + " -> BROKEN PIPE ON THEIR END")

			self.close_socket(socket, selector_obj)
		self.stream_print("\tNotifiying %d SINK       sockets and removing"%(len(self.sink_sockets)))
		while (len(self.sink_sockets) > 0):
			socket = self.sink_sockets[0]

			try: 
				socket.sendall(msg)
			except:
				self.stream_print("ERROR NOTIFYING" + self.print_socket(socket) + " -> BROKEN PIPE ON THEIR END")

			self.close_socket(socket, selector_obj)
		self.stream_print("\tNotifiying %d SOURCE     sockets and removing"%(len(self.src_sockets)))
		while (len(self.src_sockets) > 0):
			socket = self.src_sockets[0]
			try: 
				socket.sendall(msg)
			except:
				self.stream_print("ERROR NOTIFYING" + self.print_socket(socket) + " -> BROKEN PIPE ON THEIR END")

			self.close_socket(socket, selector_obj)
		
		self.print_state()
	
	def intiate_kill(self, socket_obj, selector_obj):
		if self.server_kill_requestor is None:
			self.server_kill_requestor = socket_obj
			try:
				socket_obj.sendall(b'SERVER KILL INITIATED -> This will take down the entire network AND SERVER, enter "yes" to proceed')
				self.kill_request_time = time.time()
			except:
				self.close_socket(socket_obj, selector_obj)
				self.server_kill_requestor = None

	def kill_server(self, socket_obj, selector_obj):
		if self.server_kill_requestor is None:
			return
		if socket_obj == self.server_kill_requestor:	
			if (time.time() - self.kill_request_time > 5):
				try:
					socket_obj.sendall(b'SERVER KILL REQUEST TIMED OUT -> INITIATE AGAIN')
				except:
					self.close_socket(socket_obj, selector_obj)
				
				self.server_kill_requestor = None
			else:
				
				self.kill_network(selector_obj)
				self.close()

	def query_users(self, socket_obj, selector_obj):
		msg = "UNDECLARED Sockets (%d): "%(len(self.undeclared_sockets))
		for socket in self.undeclared_sockets:
			msg += self.print_socket(socket)

		msg += " | SINK Sockets (%d): "%(len(self.sink_sockets))
		for socket in self.sink_sockets:
			msg += self.print_socket(socket)

		msg += " | SRC Sockets (%d): "%(len(self.src_sockets))
		for socket in self.src_sockets:
			msg += self.print_socket(socket)
	
		try:
			socket_obj.sendall(msg.encode('utf-8'))
		except:
			self.close_socket(socket_obj, selector_obj)		

	def recv_new_packet(self, socket_obj, selector_obj):
		if (not(self.alive)):
			return
		data_packet = b''
		try:
			data_packet = socket_obj.recv(4096)
		except:
			self.stream_print("ERROR READING FROM" + self.print_socket(socket_obj))
			return None
		if (not(data_packet)):
			#Data is empty; socket closed by them
			self.stream_print("Empty data recieved, closing socket to" + self.print_socket(socket_obj))
			self.close_socket(socket_obj, selector_obj)
			self.print_state()
			return None
		network_kill = "KILL STREAM"
		server_kill = "KiLl S3rVer"
		confirm_kill = "yes"
		report_users = "users?"	
		if data_packet.find(network_kill.encode('utf-8')) != -1:
				self.kill_network(selector_obj)
				return None
		
		if data_packet.find(server_kill.encode('utf-8')) != -1:
				self.intiate_kill(socket_obj, selector_obj)
				return None

		if data_packet.find(confirm_kill.encode('utf-8')) != -1:
				self.kill_server(socket_obj, selector_obj)

		if data_packet.find(report_users.encode('utf-8')) != -1:
				self.query_users(socket_obj, selector_obj)
				return None
		
		#Data is not empty or kill switch. Check to see where data came from and where it should go
		if socket_obj in self.undeclared_sockets:
			sink = b'sink'
			src = b'src'
			if (data_packet.find(sink) != -1):
				#'Sink' is found with in raw byte stream
				self.stream_print("Undeclared Socket" + self.print_socket(socket_obj) + " registering as SINK")
				self.undeclared_sockets.remove(socket_obj)
				self.sink_sockets.append(socket_obj)
				self.print_state()
			elif (data_packet.find(src) != -1):
				self.stream_print("Undeclared Socket" + self.print_socket(socket_obj) + " registering as SRC")
				self.undeclared_sockets.remove(socket_obj)
				self.src_sockets.append(socket_obj)
				self.print_state()
			else:
				self.stream_print("UNRECOGNIZED MESSAGE from undeclared socket " + self.print_socket(socket_obj))
				return_msg = b'REGISTER PROCESS UNSUCCESSFUL -> unrecognized command. Check command and send again'
				try:
					socket_obj.sendall(return_msg)
				except:
					#Broken Pipe error; Socket no longer connected
					self.close_socket(socket, selector_obj)
					
			return None
			
		elif socket_obj in self.sink_sockets:
			direction = SINK2SRC
			return (data_packet, direction)

		elif socket_obj in self.src_sockets:
			direction = SRC2SINK
			return (data_packet, direction)
		else:
			return None
		
		

#====================================== Functions ==================================================
def listen(telem_stream, video_stream, selector_obj):
	while video_stream or telem_stream:
		events = selector_obj.select(timeout=None)#BLOCKING, can set timeout to not block
		for key, mask in events:
			socket_obj = key.fileobj
			if key.data is None:
				print("CONNECTION ATTEMPT")
				if socket_obj == video_stream.server_socket:
					video_stream.handle_connection(selector_obj)
				if socket_obj == telem_stream.server_socket:
					telem_stream.handle_connection(selector_obj)

			if key.data is not(None) and mask == selectors.EVENT_READ|selectors.EVENT_WRITE:
				socket_obj = key.fileobj
				if (key.data == video_stream.server_socket and video_stream):

					new_packet = video_stream.recv_new_packet(socket_obj, selector_obj)

					if new_packet is not None:
						THREAD_LOCK.acquire()
						video_stream.add_to_buffer(new_packet[0], new_packet[1])
						THREAD_LOCK.release()

				if (key.data == telem_stream.server_socket and telem_stream):

					new_packet = telem_stream.recv_new_packet(socket_obj, selector_obj)

					if new_packet is not None:
						THREAD_LOCK.acquire()
						telem_stream.add_to_buffer(new_packet[0], new_packet[1])
						THREAD_LOCK.release()


	return


def send_data(telem_stream, video_stream, selector_obj):
	while video_stream or telem_stream:
		direction = SRC2SINK
		if (video_stream.mode & direction != 0):

			THREAD_LOCK.acquire()
			msg = video_stream.pull_sample(direction)
			THREAD_LOCK.release()
			
			if msg is not None:
				video_stream.send_packet(msg, direction, selector_obj)
				
				video_stream.write_to_file(msg, direction)			

		if (telem_stream.mode & direction != 0):

			THREAD_LOCK.acquire()
			msg = telem_stream.pull_sample(direction)
			THREAD_LOCK.release()
			
			if msg is not None:
				telem_stream.send_packet(msg, direction, selector_obj)
				
				telem_stream.write_to_file(msg, direction)
				
		direction = SINK2SRC
		if (telem_stream.mode & direction != 0):

			THREAD_LOCK.acquire()
			msg = telem_stream.pull_sample(direction)
			THREAD_LOCK.release()
			
			if msg is not None:
				telem_stream.send_packet(msg, direction, selector_obj)
				
				telem_stream.write_to_file(msg, direction)

		if (video_stream.mode & direction != 0):

			THREAD_LOCK.acquire()
			msg = video_stream.pull_sample(direction)
			THREAD_LOCK.release()
			
			if msg is not None:
				video_stream.send_packet(msg, direction, selector_obj)
				
				video_stream.write_to_file(msg, direction)	
		
	

#==================================================== CODE ==============================================

#def __init__(self, name, server_IP, server_port, selector_obj, src2sink_file, sink2src_file, mode, buffer_thresh):

sel = selectors.DefaultSelector()

video_file = store_dir + '/video_stream_recording.h264'
telem_file = store_dir + '/telemetry_stream.txt'
command_file = store_dir + '/command_stream.txt'

#Create stream objects
video_stream_obj = server_stream('VIDEO', SERVER_IP, SERVER_VID_PORT, sel, video_file, None, SRC2SINK, 10000)
telem_stream_obj = server_stream('TELEMETRY',SERVER_IP, SERVER_TELEM_PORT, sel, telem_file, command_file, DUPLEX, 2000)

video_stream_obj.alive = True

listen_thread = Thread(target=listen, args = (telem_stream_obj, video_stream_obj, sel))
send_thread = Thread(target=send_data, args = (telem_stream_obj, video_stream_obj, sel))

listen_thread.start()
send_thread.start()				

print("Threads are running")

last_time = time.time()
while video_stream_obj or telem_stream_obj:

	if (time.time() - last_time) > 600 and send_email:
		new_ip = subprocess.Popen(['curl', 'ifconfig.me'], stdout=subprocess.PIPE).communicate()[0]
		new_ip = new_ip.decode('utf-8')
		if (new_ip != ipaddr_a):
			smtpServer = open_smtpserver()
			my_ip_a = "Rocket Server current Global IP: %s"%(new_ip)
			msg = MIMEText(my_ip_a)
			msg['Subject'] = 'CHANGED Global IP for Rocket Server'
			msg['From'] = gmail_user
			msg['To'] = to
			smtpServer.sendmail(gmail_user, [to], msg.as_string())
			smtpServer.quit()

		ipaddr_a = new_ip
		last_time = time.time()




