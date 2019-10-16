import socket
import sys

HOST = ''
PORT = 4000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created")

try:
	sock.bind((HOST, PORT))
except socket.error, msg:
	print("Bind Failed. Exiting")
	sys.exit()

print("Socket Binded")

sock.listen(3)
print("Socket Listening for Connections")

conn, addr = sock.accept() #this call blocks!

print("Connected with %s:%d"%(addr[0],addr[1]))

while True:
	data = conn.recv(1024)
	if not data:
		break
	else:
		print data
conn.close()
print("Client Closed Connection")
print("Closing socket and exiting")
sys.exit()
