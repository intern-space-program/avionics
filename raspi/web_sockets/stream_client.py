import socket
import sys
import time
#=============================================================================================
#Command for live streaming with gstreamer
#	gst-launch-1.0 -v tcpclientsrc port=4000 host=73.136.139.198 ! h264parse ! avdec_h264 ! videoconvert ! autovideosink
#=============================================================================================

SERVER_IP = '73.136.139.198'
SERVER_PORT = 4000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Client Socket Created")

sock.connect((SERVER_IP, SERVER_PORT))
print("Client Connected to Server!\nWAITING FOR VIDEO")

video_file = "/home/ronnie/streamed_vid.h264"
video_handle = open(video_file, "wb")

packet_cnt = 0

while True:
	data = sock.recv(4096)
	if not data:
		print("Server Closed Connection")
		break
	else:
		video_handle.write(data)
		packet_cnt += 1
		print("Recieved Packet %d"%(packet_cnt))
print("Exiting")
