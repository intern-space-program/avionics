#script simulates "realistic" trajectories - DOES NOT MODEL THE AERODYNAMICS OF THE ROCKET
#	inputs:
#		- thrust curve
#	outputs:
#		- rocket state at each time step: 3DOF position, 3DOF velocity, 3DOF angle, 3DOF angular velocity
#		- ideal sensor values based on rocket state
#		- sensor output with noise, resolution, and clipping added
from math import cos
from math import sin
import time

class state_variable:
	
	def __init__(self, X, Y, Z):
		self.X = X
		self.Y = Y
		self.Z = Z

class model_params:

	def __init__(self):
		self.max_phi = 0.524 #radians (about 30 degrees)
		self.max_phi_accel = 0.1 # rad/s/time_step
		self.max_theta_accel = 0.1 #rad/s/time_step
		self.time_step = 0.01 #seconds
		self.gravity = 9.8 #m/s^2

class rocket: 
	
	def __init__(self):
		self.position = state_variable(0.0, 0.0, 0.0) #m
		self.velocity_vec = state_variable(0.0, 0.0, 0.0) #m/s
		self.accel_vec = state_variable(0.0, 0.0, 0.0) #m/s^2
		self.orientation = state_variable(0.0, 0.0, 0.0) #radians
		self.angular_velocity =  state_variable(0.0, 0.0, 0.0)
		self.phi = 0.0 # angle from Z axis
		self.phi_rate = 0.0
		self.theta = 0.0 # angle from X axis
		self.theta_rate = 0.0
		self.accel = 0.0 #m/s^2 magnitude pointing in direction of the rocket
		self.velocity = 0.0 #m/s magnitude pointing in direction of the rocket
		self.drag_const = 0 #0.5*Cd*A*p combined into one
		self.thrust = 0.0 #Newtons
		self.mass = 1 #Kg
		self.model = model_params()
	
	def set_state(self):
		self.accel_vec.Z = self.accel*cos(self.phi)
		self.accel_vec.X = self.accel*sin(self.phi)*cos(self.theta)
		self.accel_vec.Y = self.accel*sin(self.phi)*sin(self.theta)

		self.velocity_vec.Z = self.velocity*cos(self.phi)
		self.velocity_vec.X = self.velocity*sin(self.phi)*cos(self.theta)
		self.velocity_vec.Y = self.velocity*sin(self.phi)*sin(self.theta)

	def update_state(self):
		self.position.X += self.velocity_vec.X*self.model.time_step+0.5*self.accel_vec.X*self.model.time_step*self.model.time_step
		self.position.Y += self.velocity_vec.Y*self.model.time_step+0.5*self.accel_vec.Y*self.model.time_step*self.model.time_step
		self.position.Z += self.velocity_vec.Z*self.model.time_step+0.5*self.accel_vec.Z*self.model.time_step*self.model.time_step		

		self.accel = -(self.drag_const*self.velocity*self.velocity/self.mass)+(self.thrust/self.mass)
		self.velocity += self.accel*self.model.time_step

		self.accel_vec.Z = self.accel*cos(self.phi) - self.model.gravity
		self.accel_vec.X = self.accel*sin(self.phi)*cos(self.theta)
		self.accel_vec.Y = self.accel*sin(self.phi)*sin(self.theta)

		self.velocity_vec.X += self.accel_vec.X*self.model.time_step
		self.velocity_vec.Y += self.accel_vec.Y*self.model.time_step
		self.velocity_vec.Z += self.accel_vec.Z*self.model.time_step
		
		self.orientation.Z = cos(self.phi)
		self.orientation.X = sin(self.phi)*cos(self.theta)
		self.orientation.Y = sin(self.phi)*sin(self.theta)

	def print_position(self):
		print("Position:\n\tX: %f | Y: %f | Z: %f"%(self.position.X, self.position.Y, self.position.Z))
	def print_velocity(self):
		print("Velocity:\n\tX: %f | Y: %f | Z: %f"%(self.velocity_vec.X, self.velocity_vec.Y, self.velocity_vec.Z))
	def print_acceleration(self):
		print("Acceleration:\n\tX: %f | Y: %f | Z: %f"%(self.accel_vec.X, self.accel_vec.Y, self.accel_vec.Z))

#initialization
test_rocket = rocket()
overall_time = 0

#starting conditions:
test_rocket.velocity = 9.8
test_rocket.phi = 0.523
test_rocket.theta = 0.0
test_rocket.set_state()

while overall_time < 2:
	print("Time: %f"%(overall_time))
	test_rocket.print_position()
	test_rocket.print_velocity()
	test_rocket.print_acceleration()
	test_rocket.update_state()
	overall_time += test_rocket.model.time_step
	print("--------------------------------------------------------------------")
	time.sleep(5*test_rocket.model.time_step)
	



		
			
			
			
		
