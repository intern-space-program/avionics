import json
import serial
from io import BytesIO
import struct
import time
from math import trunc
import sys

max_int = ( 1 << 32) - 1
baudrate = 9600
serial_port = "/dev/ttyACM0" #USB port
serial_port = "/dev/ttyAMA0" #UART serial pins

def decompose_into_bytes(dec_val):
	base = 16777216
	byte_list = []
	for order in range(0,4):
		mult = trunc(float(dec_val)/float(base))
		byte_list.append(mult)
		dec_val = dec_val - mult*base
		base = base/256
	return byte_list
	

def form_packet(JSON_obj):
	try:
		packet_info = JSON_obj["hdr"]
		packet_num = packet_info[0]
		time_stamp = packet_info[1]
		imu_data = JSON_obj["imu"]
		gps_data = JSON_obj["gps"]
		alt_data = JSON_obj["tpa"]
	except:
		return False
	
	all_data = [imu_data, gps_data, alt_data]

	packet_bytes = bytearray([192, 222]) #0xC0DE in hex (BEGINNING OF PACKET)
	packet_bytes += bytearray(decompose_into_bytes(packet_num))
	packet_bytes += bytearray(decompose_into_bytes(time_stamp))
	for data_lists in all_data:
		for data in data_lists:
			packet_bytes += bytearray(struct.pack("f", data))
	packet_bytes += bytearray([237, 12]) #0xED0C in hex (END OF PACKET)
	return packet_bytes

def connect_to_teensy():
	connect_cnt = 0
	connected = False
	while (not(connected)):
		try:
			ser = serial.Serial(serial_port, baudrate, timeout = 0.2)
			print("Teensy Connected!")
			connected = True
		except:
			connect_cnt += 1 
			print("Trying to Connect: Attempt #%d"%(connect_cnt))
			time.sleep(0.5)
			if connect_cnt == 100:
				print("Teensy not found, Exiting")
				sys.exit()
	return ser


ser = connect_to_teensy()

telem_buff = BytesIO()

sample_JSON= {"imu": [1.0, 0.5, 0.25, 0.125, 0.0625], "gps": [1.0, 34.6758, 78.99585], "alt": [1.0, 1029283]}
sample_JSON_str = json.dumps(sample_JSON)

while True:
	try:
		JSON_packet = ser.readline()
	except:
		print("Teensy Stream Interrupted")
		ser.close()
		ser = connect_to_teensy()

	print("New Packet: %s"%(JSON_packet))
	if (len(JSON_packet)):
		corrupt = False
		try:
			JSON_obj = json.loads(JSON_packet)
		except:
			print("Error Creating JSON Obj; Invalid String")
			corrupt = True
			pass
		if (not(corrupt)):
			packet_Bytes = form_packet(JSON_obj)
			if (not(packet_Bytes)):
				print("ERROR: dirty little packet ;)")
			else:
				#telem_buff.write(packet_Bytes)
				packet_cnt += 1
				print("Current Packet | Size(%d):"%(len(packet_Bytes)))
				print(packet_Bytes)
				#print("Buffer | Size(%d):"%(telem_buff.getbuffer().nbytes))
				#print(buff.getvalue())
				print("\n\n")
		
		
		
