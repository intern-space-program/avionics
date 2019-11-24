import socket
import selectors
import threading
import os
import sys

telem_sock_alive = True
vid_sock_alive = True

def get_user_input(vid_sock, telem_sock):
	global telem_sock_alive
	global vid_sock_alive
	while True:
		new_input = input("")
		if new_input.find("vid") != -1:
			new_input = new_input.replace("vid", "")
			if new_input.find("kill") != -1:
				vid_sock.sendall(b'KILL STREAM')
				print("Kill statement sent")
			else:
				try:
					vid_sock.sendall(new_input.encode('utf-8'))
					print("Message sent on VIDEO socket")
				except:
					vid_sock_alive = False
					vid_sock.close()
					
		elif new_input.find("telem") != -1:
			new_input = new_input.replace("telem", "")
			if new_input.find("kill") != -1:
				telem_sock.sendall(b'KILL STREAM')
				print("Kill statement sent")
			else:
				try:
					telem_sock.sendall(new_input.encode('utf-8'))
					print("Message sent on TELEMETRY socket")
				except:
					telem_sock_alive = False
					telem_sock.close()
		else:
			print("Invalid Command: please include 'vid' or 'telem' in message")
	

SERVER_IP = '10.0.0.178'
SERVER_VIDEO_PORT = 5000
SERVER_TELEM_PORT = 5001

while True:
	ip_address = input("Enter the local or global ip address: ")
	SERVER_IP = ip_address
	try:
		client_vid_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client_vid_sock.connect_ex((SERVER_IP, SERVER_VIDEO_PORT))
		client_vid_sock.setblocking(False)
		print("VIDEO SOCKET CONNECTED")

		client_telem_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client_telem_sock.connect_ex((SERVER_IP, SERVER_TELEM_PORT))
		client_telem_sock.setblocking(True)
		print("TELEMETRY SOCKET CONNECTED")
		break
	except:
		print("Unable to connect. Check ip")

sel = selectors.DefaultSelector()
sel.register(client_vid_sock, selectors.EVENT_READ|selectors.EVENT_WRITE, data = 'VIDEO')
sel.register(client_telem_sock, selectors.EVENT_READ|selectors.EVENT_WRITE, data = 'TELEMETRY')

message_send = threading.Thread(target = get_user_input, args = (client_vid_sock, client_telem_sock), daemon=True)
message_send.start()
print("Waiting for user input (specify 'vid' or 'telem' in message):\n")
while vid_sock_alive or telem_sock_alive:
	events = sel.select(timeout=0.1)#BLOCKING, can set timeout to not block
	for key, mask in events:
		socket_obj = key.fileobj
		if key.data is not(None) and mask == selectors.EVENT_READ|selectors.EVENT_WRITE:
			if key.data == 'VIDEO':
				if vid_sock_alive:
					new_data = socket_obj.recv(4096)
					if not(new_data):
						print("%s: Pipe Broken, closing socket"%(key.data))
						sel.unregister(socket_obj)
						socket_obj.close()
						vid_sock_alive = False

					else:
						search = "KILL STREAM"
						if new_data.find(search.encode('utf-8')) != -1:
							print("%s: KILL SWITCH RECIEVED -> CLOSING SOCKET"%(key.data))
							sel.unregister(socket_obj)
							socket_obj.close()
							vid_sock_alive = False
						else:
							print("%s: %s"%(key.data, new_data))


				else:
					sel.unregister(socket_obj)
					socket_obj.close()

			if key.data == 'TELEMETRY':
				if telem_sock_alive:
					new_data = socket_obj.recv(4096)
					if not(new_data):
						print("%s: Pipe Broken, closing socket"%(key.data))
						sel.unregister(socket_obj)
						socket_obj.close()
						telem_sock_alive = False


					else:
						search = "KILL STREAM"
						if new_data.find(search.encode('utf-8')) != -1:
							print("%s: KILL SWITCH RECIEVED -> CLOSING SOCKET"%(key.data))
							sel.unregister(socket_obj)
							socket_obj.close()
							telem_sock_alive = False
						else:
							print("%s: %s"%(key.data, new_data))


				else:
					sel.unregister(socket_obj)
					socket_obj.close()
print("Ending Program")



