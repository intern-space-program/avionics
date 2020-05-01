import socket
from random import randint
import time
import subprocess

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

def find_ip_for_interface(interface):
	for addr in ip_addresses:
		if addr[0].find(interface) != -1:
			return addr[1]
	return None
			
def print_wireless_interfaces():
	print("List of Active Wireless Interfaces")
	for addr in ip_addresses:
		print("\t%s: %s"%(addr[0], addr[1]))

class stream_metrics:
	def __init__(self, name):
		self.name = name
		self.time_sum = 0.0
		self.max_time = 0.0
		self.min_time = 10000.0
		self.total_bytes_sent = 0

	def update_metrics(self, bytes_sent, single_time):
		self.time_sum += single_time
		self.total_bytes_sent += bytes_sent
		if single_time < self.min_time:
			self.min_time = single_time
		if single_time > self.max_time:
			self.max_time = single_time

	def print_metrics(self):
		print("%s Stream"%(self.name))
		print("%d Bytes sent in %.5f seconds"%(self.total_bytes_sent, self.time_sum))
		print("\tMAX Send Time: %f"%(self.max_time))
		print("\tMIN Send Time: %f"%(self.min_time))
		print("\tAverage Bit Rate (kbps): %d"%(int(self.total_bytes_sent*8/(self.time_sum*1000))))

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
			print("Here is a list of active interfaces")
			for addr in ip_addresses:
				print("\t",addr[0])
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

print("Telem and Video Ports connected to server. Registering as Source")

telem_sock.sendall(b'src')
video_sock.sendall(b'src')

#Test Packet Creation
test_list = []
for j in range(0, 2):
	for i in range(0, 255):
		test_list.append(i)

telem_packet = bytearray(test_list)

test_list = []
for j in range(0, 23):
	for i in range(0, 255):
		test_list.append(i)
video_packet = bytearray(test_list)

#Network Metric Variables
telem_metrics = stream_metrics("TELEMETRY")
video_metrics = stream_metrics("VIDEO")


packet_cnt = 0
program_start = time.time()

while packet_cnt < 100:
	packet_cnt += 1
	
	print("Sending packets %d"%packet_cnt)
	telem_start = time.time()
	telem_sock.sendall(telem_packet)
	telem_time = time.time()-telem_start
	telem_metrics.update_metrics(len(telem_packet), telem_time)
	time.sleep(0.05)

	video_start = time.time()
	video_sock.sendall(video_packet)
	video_time = time.time()-video_start
	video_metrics.update_metrics(len(video_packet), video_time)
	time.sleep(0.05)

program_time = time.time() - program_start
time.sleep(1.0)
telem_sock.sendall(b'KILL STREAM')
video_sock.sendall(b'KILL STREAM')

print("Stream Ended")
print("Full program time: %f"%(program_time))
print("Program Usage:")
print("\tTelemetry Stream: %.2f%%"%(telem_metrics.time_sum*100/program_time))
print("\tVideo Stream:     %.2f%%"%(video_metrics.time_sum*100/program_time))

telem_metrics.print_metrics()
video_metrics.print_metrics()












