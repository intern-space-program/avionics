import subprocess
import time
import sys
import os

start = time.time()
ok = b'0x50000'
low_voltage = b'0x50005'
store_file = 'battery_time.txt'
store = open(store_file, 'w')

def get_status():
	test = subprocess.Popen(['/opt/vc/bin/vcgencmd', 'get_throttled'], stdout=subprocess.PIPE)
	output = test.communicate(0)[0]
	output_val = output.split(b'=')[1].split(b'\n')[0]
	return output_val
last_log = -1
while True:
	status = get_status()
	current_time = int(time.time()-start)
	if (current_time%535 == 0 and current_time != last_log):
		last_log = current_time
		hrs = int(current_time/3600)
		minu = int((int(current_time)%3600)/60)
		sec = int(current_time - hrs*3600 - minu*60)
		store.write("Still Alive: %d hrs %d min %d sec\n"%(hrs,minu,sec))
	if (status == low_voltage):
		#print("LOW VOLTAGE; Starting Timer")
		restored = False
		low_start = time.time()
		low_time = time.time()-low_start
		while (low_time < 10):
			status = get_status()
			if status == ok:
				#print("Voltage restored")
				restored = True
				break
			low_time = time.time()-low_start
		if (not(restored)):
			#print("Timer Ran out. Insufficient power, Shutting down system")
			#store program time and shutdown here
			prog_time = time.time()-start
			hrs = int(prog_time/3600)
			minu = int((int(prog_time)%3600)/60)
			sec = int(prog_time - hrs*3600 - minu*60)
			store.write("Battery lasted: %d hrs %d min %d sec"%(hrs,minu,sec))
			store.close()
			os.system("sudo shutdown -h now")
			#sys.exit()
			
			
