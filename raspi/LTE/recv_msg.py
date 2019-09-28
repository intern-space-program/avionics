from Hologram.HologramCloud import HologramCloud
import time
import os


credentials = {'devicekey': '8K0Dyq*7'}

hologram = HologramCloud(credentials, network='cellular')



connected = 0
while not(connected == 1):
	os.system("sudo hologram network disconnect")
	if connected == 0:
		print "Not Connected (%d)\n -> Connecting"%(connected)
		hologram.network.connect(timeout = 10)
	else:
		print "Trying to Reconnect (%d)"%(connected)
		hologram.network.disconnect()
		hologram.network.connect(timeout = 10)
	connected  = hologram.network.getConnectionStatus()
print "Connected!"

hologram.openReceiveSocket()
time.sleep(10)

print "Ready for message"

cnt = 0
while True:
	recv_msg = hologram.popReceivedMessage()
	if (type(recv_msg) == str):
		if len(recv_msg) != 0:
			cnt+=1
			print "Message #%d: %s"%(cnt, recv_msg)
			if recv_msg == "quit":
				print "Exit message received\n ->Breaking"
				break
print "Closing Socket and disconnecting"
hologram.closeReceiveSocket()
hologram.network.disconnect()
print "Ending program"

 
