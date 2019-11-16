#model assumes thruster in a specific location and the rocket always points toward the resultant of the velocity
#thrust and drag always act in opposite direction and follow the resultant of velocity

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

	def __bool__(self):
		if self.position[ZEROTH_ORDER][Z] > -0.001:
			return True
		else:
			return False

	def transpose_ground_frame_to_rocket_frame(self):
		self.velocity = sqrt(math.pow(self.position[FIRST_ORDER][X],2)+math.pow(self.position[FIRST_ORDER][Y],2)+math.pow(self.position[FIRST_ORDER][Z],2))
		self.accel = sqrt(math.pow(self.position[SECOND_ORDER][X],2)+math.pow(self.position[SECOND_ORDER][Y],2)+math.pow(self.position[SECOND_ORDER][Z],2))

		for order in range(0,3):
			self.phi[order] = math.acos(angle[order][Z])
			if (angle[order][Y] >= 0):
				self.theta[order] = math.acos(angle[order][X]/sin(self.phi[order]))
			if (angle[order][Y] < 0):
				self.theta[order] = 2*PI - math.acos(angle[order][X]/sin(self.phi[order]))

	def transpose_rocket_frame_to_ground_frame(self):

		for order in range(0,3):
			self.angle[order][Z] = cos(self.phi[order])
			self.angle[order][X] = sin(self.phi[order])*cos(self.theta[order])
			self.angle[order][Y] = sin(self.phi[order])*sin(self.theta[order])

		for DOF in range(0,3):
			self.position[FIRST_ORDER][DOF] = self.velocity*self.angle[ZEROTH_ORDER][DOF]
			self.position[SECOND_ORDER][DOF] = self.accel*self.angle[ZEROTH_ORDER][DOF]

		"""self.position[FIRST_ORDER][Z] = self.velocity*cos(self.phi[ZEROTH_ORDER])
		self.position[FIRST_ORDER][X] = self.velocity*sin(self.phi[ZEROTH_ORDER])cos(self.theta[ZEROTH_ORDER])
		self.position[FIRST_ORDER][Z] = self.velocity*sin(self.phi[ZEROTH_ORDER])sin(self.theta[ZEROTH_ORDER]) 
		self.position[SECOND_ORDER][Z] = self.accel*cos(self.phi[ZEROTH_ORDER])
		self.position[SECOND_ORDER][X] = self.accel*sin(self.phi[ZEROTH_ORDER])cos(self.theta[ZEROTH_ORDER])
		self.position[SECOND_ORDER][Z] = self.accel*sin(self.phi[ZEROTH_ORDER])sin(self.theta[ZEROTH_ORDER])"""

	def print_position_vec(self, order):
		print("%s:\n\tX: %f | Y: %f | Z: %f"%(self.position_name[order], self.position[order][X], self.position[order][Y], self.position[order][Z]))

	def print_angle_vec(self, order):
		print("%s:\n\tX: %f | Y: %f | Z: %f"%(self.angle_name[order], self.angle[order][X], self.angle[order][Y], self.angle[order][Z]))

	def print_rocket_frame(self):
		print("Positional:\n\tVelocity:     %f\n\tAcceleration: %f"%(self.velocity, self.accel))
		print("Angular:\n\tPhi:   %f | %f\n\tTheta: %f | %f"%(self.phi[ZEROTH_ORDER], (self.phi[ZEROTH_ORDER]*180/PI), self.theta[ZEROTH_ORDER], (self.theta[ZEROTH_ORDER]*180/PI)))

	def print_flight_metrics(self):
		print("Max Height:              %f m"%(self.max_height))
		print("Max Speed:               %f m/s"%(self.max_speed))
		print("Max Velocity:            %f m/s"%(self.max_velocity))
		print("Max Acceleration(mag):   %f m/s^2"%(self.max_acceleration_mag))
		print("Max Acceleration(DOF):   %f m/s^2"%(self.max_acceleration_DOF))
		print("\nFlight Time:             %f s"%(self.flight_time))
		print("Distance from Pad:       %f m"%(self.distance_from_pad))

	def time_step_print(self):
		print("Time: %f"%(self.overall_time))
		for order in range(0,3):
			self.print_position_vec(order)
			self.print_rocket_frame()
		print("----------------------------------------------------------------------------")
		time.sleep(5*self.model.time_step)

	def update_metrics(self):
		
		self.flight_time = self.overall_time

		if self.velocity > self.max_speed:
			self.max_speed = self.velocity

		if self.position[ZEROTH_ORDER][Z] > self.max_height:
			self.max_height = self.position[ZEROTH_ORDER][Z]

		for DOF in range(0,3):
			if abs(self.position[FIRST_ORDER][DOF]) > self.max_velocity:
				self.max_velocity = abs(self.position[FIRST_ORDER][DOF])
			if abs(self.position[SECOND_ORDER][DOF]) > self.max_acceleration_DOF:
				self.max_acceleration_DOF = abs(self.position[SECOND_ORDER][DOF])

		accel_result = sqrt(math.pow(self.position[SECOND_ORDER][X],2)+math.pow(self.position[SECOND_ORDER][Y],2)+math.pow(self.position[SECOND_ORDER][Z],2))
		if accel_result > self.max_acceleration_mag:
			self.max_acceleration_mag = accel_result

		self.distance_from_pad = sqrt(math.pow(self.position[ZEROTH_ORDER][X], 2) + math.pow(self.position[ZEROTH_ORDER][Y], 2))

	def update_state(self):

		self.update_metrics()

		#update 1 Dimension acceleration for forces in direction of the rocket
		self.accel = (-self.drag_const*self.velocity*self.velocity + self.thrust)/self.mass

		#add random angle noise here
		#propgate that through accel and vel to position

		#update 3DOF angle based on phi and theta at time t
		for order in range(0,1):
			self.angle[order][Z] = cos(self.phi[order])
			self.angle[order][X] = sin(self.phi[order])*cos(self.theta[order])
			self.angle[order][Y] = sin(self.phi[order])*sin(self.theta[order])

		#break acceleration magnitude into 3 DOF accel and add 3DOF forces/accelerations
		for DOF in range(0,3):
			self.position[SECOND_ORDER][DOF] = self.accel*self.angle[ZEROTH_ORDER][DOF]
			self.position[SECOND_ORDER][Z] -= self.model.gravity

		#Acceleration(t) and velocity(t) update position(t+1)
		#Acceleration(t) updates velocity(t+1)
		for DOF in range(0,3):
			self.position[ZEROTH_ORDER][DOF] += self.position[FIRST_ORDER][DOF]*self.model.time_step + 0.5*self.position[SECOND_ORDER][DOF]*self.model.time_step*self.model.time_step
			self.position[FIRST_ORDER][DOF] += self.position[SECOND_ORDER][DOF]*self.model.time_step

		#Get Velocity(t+1) magnitude
		self.velocity = sqrt(math.pow(self.position[FIRST_ORDER][X],2)+math.pow(self.position[FIRST_ORDER][Y],2)+math.pow(self.position[FIRST_ORDER][Z],2))

		#Update phi(t+1) and theta(t+1) based on velocity(t+1) resultant
		temp_theta = math.atan((self.position[FIRST_ORDER][Y]/(self.position[FIRST_ORDER][X]+0.0000001)))
		if (self.position[FIRST_ORDER][X] < 0):
			#Quadrant II and III
			temp_theta = PI + temp_theta
		if (self.position[FIRST_ORDER][X] >= 0):
			#Quadrant I and IV
			temp_theta = 2*PI + temp_theta
		self.theta[ZEROTH_ORDER] = temp_theta

		self.phi[ZEROTH_ORDER] = math.acos((self.position[FIRST_ORDER][Z]/(self.velocity+0.000001)))

		self.overall_time += self.model.time_step

		if self.print_each_step:
			self.time_step_print()

test_rocket = rocket(9.8, 0, 0.01, 0.0)
test_rocket.transpose_rocket_frame_to_ground_frame()
list_x = []
list_y = []
list_z = []
while (test_rocket):
	list_x.append(test_rocket.position[ZEROTH_ORDER][X])
	list_y.append(test_rocket.position[ZEROTH_ORDER][Y])
	list_z.append(test_rocket.position[ZEROTH_ORDER][Z])

	if (test_rocket.overall_time < 2):
		test_rocket.thrust = 80.0
	else:
		test_rocket.thrust = 0.0
	test_rocket.update_state()

print("Simulation Ended")
test_rocket.print_flight_metrics()
print("PROGRAM TIME: %f s"%(time.time()-start_time))



