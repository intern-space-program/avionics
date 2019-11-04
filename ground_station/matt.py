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
	def update(self, dt):
		self.ids.telemetry1.text = 'telemetry1: ' + str(random.randint(0,200))
		self.ids.telemetry2.text = 'telemetry2: ' + str(random.randint(0,200))
		self.ids.telemetry3.text = 'telemetry3: ' + str(random.randint(0,200))
		self.ids.telemetry4.text = 'telemetry4: ' + str(random.randint(0,200))
	def on_touch_up(self, touch):
		Clock.schedule_interval(self.update,0.5)
	pass

class Status(Label):
	pass

class Screen(FloatLayout):
	pass

class Plot(GridLayout): 
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	(ox,oy,oz) = (0,0,0)
	def addPlot(self):
		self.ax.set_xlim3d([0.0, 10.0])
		self.ax.set_ylim3d([0.0, 10.0])
		self.ax.set_zlim3d([0.0, 10.0])
		self.add_widget(self.fig.canvas)
		return self

	def animate(self, i):
		input = open('location.txt','r').read()
		x, y, z = input.split(',')
		if (x,y,z) != (self.ox,self.oy,self.oz):
			(self.ox, self.oy, self.oz) = (x,y,z)
			self.ax.scatter(float(x),float(y),float(z), 'o', color='red')
			self.fig.canvas.draw_idle()

	def on_touch_up(self, touch):
		Clock.schedule_interval(self.animate,0.5)


	pass

class MyGrid(GridLayout):
	def build(self):
		self.add_widget(Video())
		self.add_widget(Plot(cols = 1).addPlot())
		self.add_widget(Telemetry())
		self.add_widget(Status())
		return self
		
	pass


class MattApp(App):

	def build(self):
		main = Screen()
		grid = MyGrid(cols = 2, size = (main.height, main.width))
		main.add_widget(grid.build())
	
		return main

MattApp().run()
