from kivy.app import App
#from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager,Screen
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from mpl_toolkits import mplot3d
from kivy.clock import Clock
import numpy as np 
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plt
import random

class Quad(Widget):
    def update_line(hl, new_data):
	    xdata, ydata, zdata = hl._verts3d
	    hl.set_xdata(list(np.append(xdata, new_data[0])))
	    hl.set_ydata(list(np.append(ydata, new_data[1])))
	    hl.set_3d_properties(list(np.append(zdata, new_data[2])))
	    plt.draw()
    def update(self,dt):
        self.ids.telemetry1.text = 'telemetry1: ' + str(random.randint(0,200))
        self.ids.telemetry2.text = 'telemetry2: ' + str(random.randint(0,200))
        self.ids.telemetry3.text = 'telemetry3: ' + str(random.randint(0,200))
        self.ids.telemetry4.text = 'telemetry4: ' + str(random.randint(0,200))
        #print(self.ids.telemetry1.text)
        #print(self)
    def on_touch_up(self, touch):
        Clock.schedule_interval(self.update,0.1)
        
    #map = plt.figure()
    #map_ax = Axes3D(map)
    #map_ax.autoscale(enable=True, axis='both', tight=True)
    ## Setting the axes properties
    #map_ax.set_xlim3d([0.0, 10.0])
    #map_ax.set_ylim3d([0.0, 10.0])
    #map_ax.set_zlim3d([0.0, 10.0])
    #hl, = map_ax.plot3D([0], [0], [0])
#
    #update_line(hl, (2,2, 1))
    #plt.show(block=False)
    #plt.pause(1)
    #
    #update_line(hl, (5,5, 5))
    #plt.show(block=False)
    #plt.pause(2)
    #
    #update_line(hl, (8,1, 4))
    #plt.show(block=True)
    #plt.pause(2)

    pass 

class QuadsApp(App):
    def build(self):
        #Clock.schedule_interval(Quad.update, 0.5)
        return Quad()

QuadsApp().run()