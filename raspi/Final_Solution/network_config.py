# This script does the following:
#	1) Checks for and disconnects any existing PPP (cell connection) threads
#	2) Begins a PPP session through a subprocess and manages the output
#	3) If successful, it disables the wifi and ends 
#	4) If unsuccessful, it will continue attempting to connect

# Author: Ronnie Ankner
# Last Edited: 11/1/19
# Libraries
#	-> os: run terminal commands from python script
#	-> subprocess: used to run and monitor terminal commands from python
#	-> sys: used to exit the program

#Note: Yes, hologram provides a python SDK, but that code is only pyhton2.X compatible. this script allows to work with hologram tools in python3 




import os
import subprocess
import sys


#======================== Connect LTE Network =================================
#Ouput messages
not_connected_msg = "ERROR: Modem not detected"
fail_msg = "Failed to start PPP"
success_msg = "PPP session started"

LTE_connected = False
os.system("sudo hologram network disconnect -v")#make sure PPP connection does not exist
while (not(LTE_connected)):
	print("Running Hologram Connect")
	#Begin a subprocess to start PPP connection and connect LTE network
	LTE_connect = subprocess.Popen(['sudo', 'hologram', 'network', 'connect', '-v'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	while True:
		out, err = LTE_connect.communicate()
		output = str(out + err)
		if (out):
			print("LTE OUTPUT: %s"%(str(out)))
		if (err):
			print("LTE ERROR: %s"%(str(err)))

		if output.find(not_connected_msg) != -1 :
			print("Modem Disconnected")
			break
		elif output.find(fail_msg) != -1 :
			print("Connection Failed")
			break
		elif output.find(success_msg) != -1:
			print("CONNECTION SUCCEEDED")
			LTE_connected = True
			break
		elif (len(output) == 0):
			print("Program Failed")
			break
		else:
			print("Undetermined Error, Exiting")
			sys.exit()

#Once LTE is connected, 
os.system("sudo ifconfig wlan0 down") #disable wifi
			

