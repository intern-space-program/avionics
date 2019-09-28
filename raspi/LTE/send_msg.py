from Hologram.HologramCloud import HologramCloud
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

msg_err = hologram.sendMessage("I'm alive", timeout = 7)
if msg_err == 0:
	print "WE OUT HERE!!!!"
else:
	print hologram.getResultString(msg_err)
