import subprocess
import os
import socket

record_file = 'buffer_recording.h264'
#Clear file
f = open(record_file, 'w')
f.close()

STREAM_IP = '127.0.0.1'
STREAM_PORT = 4000
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_udp(msg):
	send_sock.sendto(msg, (STREAM_IP, STREAM_PORT))

#Set Up subprocess
record_file_path = '/home/pi/Intern_Space_Program_Git/F2019_Avionics/raspi/Camera/' + record_file
print 'Listening to ' + record_file_path
LTE_proc = subprocess.Popen(['tail', '-f', record_file_path], stdout = subprocess.PIPE)

data_total = 0

while True:
	data_in = LTE_proc.stdout.readline()
	if len(data_in) > 0:
		send_udp(data_in)
		data_total += len(data_in)
		print "Total Cumulative Data (B): %d"%(data_total)
