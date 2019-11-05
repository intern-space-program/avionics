import socket
import selectors
from io import BytesIO

SERVER_IP = ''
SERVER_VID_PORT = 5000
SERVER_TELEM_PORT = 5001

video_ports = [SERVER_VID_PORT]
telem_ports = [SERVER_TELEM_PORT]

stream_status = [1,1] #video, telemetry

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

def accept_connection(socket_obj):
	conn, addr = socket_obj.accept()
	conn.setblocking(False)
	if (name_source(socket_obj) == 'VIDEO'):
		video_ports.append(addr[1])
	if (name_source(socket_obj) == 'TELEMETRY'):
		video_ports.append(addr[1])
	print("%s Stream connected to %s:%d"%(name_source(socket_obj), addr[0], addr[1]))
	data = types.SimpleNamespace(addr=addr, inb=b'', outb = b'')
	events = selectors.EVENT_READ | selectors.EVENT_WRITE
	sel.register(conn,events, data=data)
	

server_vid_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_vid_sock.bind((SERVER_IP, SERVER_VID_PORT))
server_vid_sock.listen()
server_vid_sock.setblocking(False)
print("%s Server Created and Listening"%(name_source(server_vid_sock)))

server_telem_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_telem_sock.bind((SERVER_IP, SERVER_TELEM_PORT))
server_telem_sock.listen()
server_telem_sock.setblocking(False)
print("%s Server Created and Listening"%(name_source(server_telem_sock)))

sel = selectors.DefaultSelector()
sel.register(server_vid_sock, selectors.EVENT_READ, data=None)
sel.register(server_telem_sock, selectors.EVENT_READ, data=None)

vid_buffer = BytesIO()
telem_buffer = BytesIO()

video_file = 'video_stream_recording.h264'
telem_file = 'telemetry_stream.txt'

video_handle = open(video_file, 'wb')
telem_handle = open(telem_file, 'wb')

vid_packet_cnt = 0
telem_packet_cnt = 0

vid_total_bytes = 0
telem_total_bytes = 0

while stream_status[0] or stream_status[1]:
	events = sel.select(timeout=None)#BLOCKING, can set timeout to not block
	for key, mask in events:
		if key.data is None:
			#initial connection attempt
			accept_connection(key.fileobj)
		else:
			#data contains information to be read
			socket_obj = key.fileobj
			recv_data = socket_obj.recv(4096)
			if (not(recv_data)):
				#Empty Data
				#Socket Connection was broken
				print("%s Stream BROKEN; Closing Connection"%(name_source(socket_obj)))
				if (name_source(socket_obj) == 'VIDEO'):
					stream_status[0] = 0
				if (name_source(socket_obj) == 'TELEMETRY'):
					stream_status[1] = 0
				socket_obj.close()
			else:
				if name_source(key.fileobj) == 'VIDEO':
					vid_packet_cnt += 1
					print("VIDEO: Recieved packet #%d: %d Bytes"%(vid_packet_cnt, len(recv_data)))
					vid_total_bytes += len(recv_data)
					#Video Data is ready
					vid_buffer.write(recv_data)
					if (vid_buffer.getbuffer().nbytes() > 10000):
						#Buffer reached thresholded size
						print("VIDEO: Buffer reached capacity; storing and clearing")
						#process data
						#-> send to local udp port for display

						#store to file
						video_handle.write(vid_buffer.get_value())

						#clear buffer
						vid_buffer.truncate(0)
						vid_buffer.seek(0)

				if name_source(key.fileobj) == 'TELEMETRY':
					#Telemetry data is ready
					telem_packet_cnt += 1
					print("TELEMETRY: Recieved packet #%d: %d Bytes"%(telem_packet_cnt, len(recv_data)))
					telem_total_bytes += len(recv_data)
					telem_buffer.write(recv_data)
					if (telem_buffer.getbuffer().nbytes() > 10000):
						#Buffer reached thresholded size
						print("TELEMETRY: Buffer reached capacity; storing and clearing")
						#process data
						#-> parse telemetry function here

						#store to file
						telem_handle.write(telem_buffer.get_value())

						#clear buffer
						telem_buffer.truncate(0)
						telem_buffer.seek(0)

				if not(name_source(key.fileobj):
					#Stream unidentified
					print("Conneciton Unidentified") 
print("Stream Ended")
print("Stream Statistics: \n\tVIDEO Bytes: %d\n\tTELEM Bytes: %d"%(vid_total_bytes, telem_total_bytes))


video_handle.close()
telem_handle.close()

server_vid_sock.close()
server_telem_sock.close()




