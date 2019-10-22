#Client: RASPI
#Server: COMPUTER

import socket
import sys
import time
#=============================================================================================
#Command for live streaming with gstreamer
#	gst-launch-1.0 -v tcpserversrc port=5000 host=73.136.139.198 ! h264parse ! avdec_h264 ! videoconvert ! autovideosink
#=============================================================================================

HOST = ''
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created")

try:
	sock.bind((HOST, PORT))
except socket.error:
	print("Bind Failed. Exiting")
	sys.exit()

print("COMPUTER SERVER Socket Binded")

video_file = "/home/ronnie/streamed_vid.h264"
video_handle = open(video_file, "wb")

#Wait for connection to client
sock.listen(3)
print("COMPUTER SERVER Listening for Connections")

conn, addr = sock.accept() #this call blocks!

print("RASPI CLIENT Connected from %s:%d"%(addr[0],addr[1]))
print("Beginning Stream!")

packet_cnt = 0

while True:
	data = conn.recv(4096)
	if not data:
		print("Client Closed Connection")
		break
	else:
		video_handle.write(data)
		packet_cnt += 1
		print("Recieved Packet %d"%(packet_cnt))
print("Closing Socket")
sock.close()
print("Exiting")
