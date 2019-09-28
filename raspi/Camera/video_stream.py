from picamera import PiCamera
from time import sleep

#Camera Settings
#camera.annotate_text = "timestamp and packet number"
camera = PiCamera()
camera.resolution = (320,240)
camera.framerate = 12

camera.start_preview()
camera.start_recording('python_Vidstream.h264')
sleep(8)
camera.stop_recording()
camera.stop_preview()
