from math import cos
from math import sin
from math import sqrt
import math
import time
start_time = time.time()
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

#============== MACROS ===============================

#state variable 'macros'
ZEROTH_ORDER = 0
FIRST_ORDER = 1
SECOND_ORDER = 2

X = 0
Y = 1
Z = 2

#Constant Macros
PI = 3.1415926535

#============== FUNCTIONS =============================
def roll(angle):
	print("ROLL %.2f degrees"%(angle*180/PI))
	trans = np.zeros((3,3))
	
	trans[X, X] = 1
	trans[X, Y] = 0
	trans[X, Z] = 0

	trans[Y, X] = 0
	trans[Y, Y] = cos(angle)
	trans[Y, Z] = sin(angle)

	trans[Z, X] = 0
	trans[Z, Y] = -sin(angle)
	trans[Z, Z] = cos(angle)

	return trans

def pitch(angle):
	print("PITCH %.2f degrees"%(angle*180/PI))	
	
	trans = np.zeros((3,3))
	
	trans[X, X] = cos(angle)
	trans[X, Y] = 0
	trans[X, Z] = -sin(angle)

	trans[Y, X] = 0
	trans[Y, Y] = 1
	trans[Y, Z] = 0

	trans[Z, X] = sin(angle)
	trans[Z, Y] = 0
	trans[Z, Z] = cos(angle)
	
	return trans

def yaw(angle):
	print("YAW %.2f degrees"%(angle*180/PI))	
	
	trans = np.zeros((3,3))

	trans[X, X] = cos(angle)
	trans[X, Y] = sin(angle)
	trans[X, Z] = 0

	trans[Y, X] = -sin(angle)
	trans[Y, Y] = cos(angle)
	trans[Y, Z] = 0

	trans[Z, X] = 0
	trans[Z, Y] = 0
	trans[Z, Z] = 1
	
	return trans

def rotate(angle):
	print("ROTATE %.2f degrees"%(angle*180/PI))	
	
	trans = yaw(angle)
	trans = trans.T
	
	return trans

def theta(angle):
	print("THETA %.2f degrees"%(angle*180/PI))	
	
	trans = yaw(angle)
	return trans

def phi(angle):
	print("PHI %.2f degrees"%(angle*180/PI))	
	
	trans = pitch(angle)
	trans = trans.T

	return trans
	

#============== CLASSES ===============================

class model_params:

	def __init__(self):
		self.max_phi = 0.524 #radians (about 30 degrees)
		self.max_phi_accel = 0.1 # rad/s/time_step
		self.max_theta_accel = 0.1 #rad/s/time_step
		self.time_step = 0.01 #seconds
		self.gravity = 9.8 #m/s^2 

class rocket:

	def __init__(self, start_v, start_a, start_phi, start_theta):

		#Rocket Frame Variables
		self.velocity = start_v #(m/s) magnitude which always points in direction of rocket
		self.accel = start_a #(m/s^2) magnitude which always points in direction of rocket
		#rocket_pos = [0, start_v, start_a] # (m, m/s, m/s^2) 3 DOF magnitude list | 0th is flight path distance, 1st is vel magnitude, 2nd is accel magnitude
		self.phi = [start_phi, 0, 0] #(radians) 3 order list | 0th order phi is clockwise angle from Z axis
		self.theta = [start_theta, 0, 0] #(radians) 3 order list | 0th order theta is clockwise angle from X axis
		self.thrust = 0.0 # (Newtons) magnitude force always in direction of the rocket

		#Rocket model properties
		self.mass = 1 #(kg)
		self.drag_const  = 0.01 #0.5*Cd*A*p all lumped together | reasonable is around 0.01 or less

		#Overall Inertial Frame Variables
		self.position = [[0,0,0],[0,0,0],[0,0,0]] # (m, m/s, m/s^2) 9DOF freedom position: 3DOF position, 3DOF velocity, 3DOF accel
		self.position_name = ["Position", "Velocity", "Acceleration"]
		self.angle = [[0,0,0],[0,0,0],[0,0,0]] # (rad, rad/s, rad/s^2) 9DOF freedom angle: 3DOF angle, 3DOF angular velocity, 3DOF angular acceleration
		self.angle_name = ["Angle", "Angular Velocity", "Angular Acceleration"]
		self.overall_time = 0.0

		#Flight Metrics
		self.max_height = 0
		self.max_speed = 0
		self.max_velocity = 0
		self.max_acceleration_mag = 0
		self.max_acceleration_DOF = 0
		self.flight_time = 0
		self.distance_from_pad = 0

		self.model = model_params()
		self.print_each_step = False

