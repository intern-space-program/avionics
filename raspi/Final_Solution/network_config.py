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
			

