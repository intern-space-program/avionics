from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color
from kivy.clock import Clock
import random

class Status(GridLayout):

    def __init__(self, **kwargs):
        instDict = {"GPS":['values',[1, 0, 0, 1]],"IMU":['values',[0, 1, 0, 1]],"ALT":['values',[0, 0, 1, 1]],"Airspeed":['values',[1, 0, 0, 1]],"LTE":['values',[1, 0, 0, 1]]}
        
        super(Status, self).__init__(**kwargs)
        self.cols = 1
        self.rows = 6
        self.add_widget(Label(text='STATUS'))
        #RED = color=[1, 0, 0, 1]
        #GREEN = [0, 1, 0, 1]
        for eachInstrument in instDict:
            self.add_widget(Label(text=eachInstrument + ': [' + instDict[eachInstrument][0] + ']', color=instDict[eachInstrument][1]))
        Clock.schedule_interval(lambda a:self.update(self), 1)
    
    def update(self,obj):
        obj.clear_widgets()
        #check to see status and store in [1]
        instDict = {"GPS":['values',[random.random(), 1, 0, 1]],"IMU":['values',[0, 0, 1, 1]],"ALT":['values',[0, 0, 1, 1]],"Airspeed":['values',[1, 0, 0, 1]],"LTE":['values',[1, 0, 0, 1]]}
        self.add_widget(Label(text='STATUS'))
        for eachInstrument in instDict:
            self.add_widget(Label(text=eachInstrument + ': ' + instDict[eachInstrument][0] + '', color=instDict[eachInstrument][1]))
    

class ISPStatusApp(App):

    def build(self):
        return Status()


if __name__ == '__main__':
    ISPStatusApp().run()