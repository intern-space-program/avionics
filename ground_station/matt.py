#Modified script. Change location.txt to add to graph

from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  
from kivy.uix.label import Label
from kivy.clock import Clock
import random
import matplotlib.animation as animation
from matplotlib import use as mpl_use

mpl_use('module://kivy.garden.matplotlib.backend_kivy')



class Video(Label):
	pass

class Telemetry(GridLayout):
	def update(self, alt, x, y, vel):
		self.ids.alt.text = alt
		self.ids.pos.text = x + ',' + y  
		self.ids.vel.text = vel
	pass

class Status(GridLayout):
	def update(self, fIMU, fGPS, fALT, fTeensy, fRaspi, fLTE, fSerial):
		self.ids.IMU.text = fIMU
		self.ids.GPS.text = fGPS
		self.ids.ALT.text = fALT
		self.ids.Teensy.text = fTeensy
		self.ids.Raspi.text = fRaspi
		self.ids.LTE.text = fLTE
		self.ids.Serial.text = fSerial
	pass

class Scran(FloatLayout):
	pass
class Seperator(FloatLayout):
	pass

class Plot(GridLayout): 
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	def addPlot(self):
		self.add_widget(self.fig.canvas)
		return self

	def update(self, x, y, z):
		self.ax.scatter(float(x),float(y),float(z), 'o', color='red')
		self.fig.canvas.draw_idle()


	pass

class MyGrid(GridLayout):
	tel = None
	plot = None
	stat = None
	(ox,oy,oz) = (0,0,0)

	def build(self):
		self.tel = Telemetry()
		self.plot = Plot(cols = 1)
		self.stat = Status()
		self.add_widget(Video())
		self.add_widget(self.plot.addPlot())
		self.add_widget(self.tel)
		self.add_widget(self.stat)


		return self
		
	def update(self,i):

		input = open('location.txt','r').read()
		x, y, z = str(random.randint(0,200)), str(random.randint(0,200)), str(random.randint(0,200))
		if (x,y,z) != (self.ox,self.oy,self.oz):
			(self.ox, self.oy, self.oz) = (x,y,z)
			self.plot.update(x, y, z)
			
		self.tel.update(x, y , z, z)
		self.stat.update('bad', 'bad', 'bad', 'bad', 'bad', 'bad', 'bad')


	pass

class MattApp(App):
	grid = None
	def build(self):
		main = Scran()
		self.grid = MyGrid(cols = 2, size = (main.height, main.width), id  = 'grid')
		main.add_widget(self.grid.build())
		main.add_widget(Seperator())
		return main
	def on_start(self):
		Clock.schedule_interval(self.grid.update, .2)
		#code here?







MattApp().run()
#wont go here