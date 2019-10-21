import socket
import sys
import time

SERVER_IP = '127.0.0.1'
SERVER_PORT = 4000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Client Socket Created")

sock.connect((SERVER_IP, SERVER_PORT))
print("Client Connected to Server!")

cnt = 10
while cnt > 0:
	sock.sendall("Closing in connection %ds"%(cnt))
	cnt-=1
	time.sleep(1)
print("Closing Connection")
sock.close()
