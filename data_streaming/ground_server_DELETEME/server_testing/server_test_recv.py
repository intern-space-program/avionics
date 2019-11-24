import socket
import selectors
import threading
import os
import sys
import subprocess
	
vid_sock_alive = True
telem_sock_alive = True

def get_ip_addrs():
	
	get_ip = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE)

	lines =  get_ip.communicate()[0].split(b'\n')
	interface = b''
	ip_addresses = [] #list of tuples containing interface and IPv4 for that interface

	for line in lines:
		if line.find(b' ') > 0:
			interface = line.split(b':')[0].decode('utf-8')

		if line.find(b'inet ') > -1:
			ip_address = line.split(b' ')[9].decode('utf-8')
			ip_addresses.append((interface, ip_address))
	return ip_addresses

ip_addresses = get_ip_addrs()

def find_ip_for_interface(interface):
	for addr in ip_addresses:
		if addr[0].find(interface) != -1:
			return addr[1]
	return None
			
def print_wireless_interfaces():
	print("List of Active Wireless Interfaces")
	for addr in ip_addresses:
		print("\t%s: %s"%(addr[0], addr[1]))

SERVER_IP = '73.115.48.151'
SERVER_VIDEO_PORT = 5000
SERVER_TELEM_PORT = 5001

print_wireless_interfaces()

while True:
	ip_address = input("Enter the local/global ip address or interface name: ")
	if ip_address.find('local') != -1:
		SERVER_IP = '127.0.0.1'
	elif (ip_address.find('wlo') != -1 or ip_address.find('wlan') != -1):
		SERVER_IP = find_ip_for_interface('wlo')
		if SERVER_IP is None:
			SERVER_IP = find_ip_for_interface('wlan')
		if SERVER_IP is None:
			print("Wireless Local interface not found -> it's either down or named differently")
			print_wireless_interfaces()
	elif find_ip_for_interface(ip_address) is not None:
		print("IP found by interface")
		SERVER_IP = find_ip_for_interface(ip_address)
	elif ip_address.find("serv") != -1:
		SERVER_IP = '73.115.48.151'
	else:
		SERVER_IP = ip_address	
	 
	try:
		video_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		video_sock.connect((SERVER_IP, SERVER_VIDEO_PORT))
		print("VIDEO SOCKET CONNECTED")

		telem_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		telem_sock.connect((SERVER_IP, SERVER_TELEM_PORT))
		print("TELEMETRY SOCKET CONNECTED")
		break
	except:
		print("Unable to connect. Check ip or interface name")

print("Telem and Video Ports connected to server. Registering as SINKS")

telem_sock.sendall(b'sink')
video_sock.sendall(b'sink')

print("Registered as sinks!")

telem_bytes = 0
vid_bytes = 0

sel = selectors.DefaultSelector()
sel.register(video_sock, selectors.EVENT_READ|selectors.EVENT_WRITE, data = 'VIDEO')
sel.register(telem_sock, selectors.EVENT_READ|selectors.EVENT_WRITE, data = 'TELEMETRY')

while vid_sock_alive or telem_sock_alive:
	events = sel.select(timeout=None)#BLOCKING, can set timeout to not block
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
							vid_bytes += len(new_data)


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
							telem_bytes += len(new_data)


				else:
					sel.unregister(socket_obj)
					socket_obj.close()
print("Ending Program")
print("VIDEO Recieved Bytes:     %d"%(vid_bytes))
print("TELEMETRY Recieved Bytes: %d"%(telem_bytes))



