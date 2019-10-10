import socket
import time


def utf8len(s):
	return len(s.encode('utf-8'))


#Open TCP Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print "Socket Created"

remote_host = 'google.com'
port = 80 #standard HTTP request port

try:
	remote_ip = socket.gethostbyname(remote_host)
except socket.gaierror:
	print "Host IP could not be acquired"
	sys.exit()

print "Host IP address: " + remote_ip
connect_start = time.time()
sock.connect((remote_ip, port))
connect_time = time.time()-connect_start

print "Socket Connected to " + remote_ip + " on port " + str(port)

#HTTP request for website data
#msg = '&quot;GET / HTTP/1.1\r\n\r\n&quot;'
msg = "I am sending a bunch of data ?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?"
sent_cnt = 0
time_sum = 0
print "Testing Latency"
while (sent_cnt < 1):
	try:
		send_start = time.time()
		sock.sendall(msg)
		send_time = (time.time()-send_start)
		time_sum += send_time
		sent_cnt += 1
		print "Sent packet #%d: %fs"%(sent_cnt, send_time)
	except socket.error:
		print "Send failed"
		sys.exit()

send_time = time_sum/float(sent_cnt)
print "Messages Sent Sucessfully!"
print "\tTime to Connect: %fs\n\tTime to Send:    %fs"%(connect_time, send_time)
print "\tMessage size: %d Bytes | %d bits"%(utf8len(msg), utf8len(msg)*8)
print "\tApparent Data Rate: %d kbps"%(int(float(utf8len(msg)*8)/(send_time*1000))) 

#print "Recieving Data"
#msg = '&quot;GET / HTTP/1.1\r\n\r\n&quot;'
#sock.sendall(msg)
#reply = sock.recv(4096)
print reply






