from picamera import PiCamera
from picamera import PiCameraCircularIO
from picamera import CircularIO
import io
from time import sleep
import os

#Global Variables
bitrate_max = 300000
record_time = 8 # Time in seconds that the recording runs for
record_chunk = 0.1 #chunk size in seconds video object is broken into and sent 
frame_rate = 20

if record_chunk < 1/frame_rate:
	record_chunk = 1/frame_rate

#Camera Settings
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = frame_rate

#Stream Object Settings
#stream = PiCameraCircularIO(camera, seconds = 10, bitrate=bitrate_max)
stream = CircularIO(int((bitrate_max*record_chunk*10)/8))
video_chunk = io.BytesIO()

#Video Recording
camera.start_preview()
camera.start_recording(stream, format='h264', bitrate=bitrate_max)
cnt = 0
while cnt < record_time/record_chunk:
	camera.wait_recording(record_chunk)
	#stream.copy_to('buffer_recording.h264')
	stream.readall()
	cnt+=1
	print(stream.getvalue())

camera.stop_recording()
camera.stop_preview()
