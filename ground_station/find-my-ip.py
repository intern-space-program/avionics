import subprocess
import time

interval = 5

while True:
   ip = subprocess.Popen(['curl', 'ifconfig.me'], stdout=subprocess.PIPE).communicate()[0]
   f = open('testip.txt', 'a')
   f.truncate(0)
   f.write(ip.decode('utf-8') + '\n')
   f.close()
   time.sleep(interval * 60)
