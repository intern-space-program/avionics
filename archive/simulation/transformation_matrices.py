import numpy as np
from math import cos
from math import sin
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


X = 0
Y = 1
Z = 2
PI = 3.1415926535

def roll(angle):
	print("ROLL %.2f degrees"%(angle*180/PI))
	trans = np.array([[1, 0, 0],[0,cos(angle),-sin(angle)],[0,sin(angle),cos(angle)]])
	print(trans)
	return trans

def pitch(angle):
	print("PITCH %.2f degrees"%(angle*180/PI))	
	trans = np.array([[cos(angle), 0, sin(angle)],[0,1,0],[-sin(angle),0,cos(angle)]])
	print(trans)
	return trans

def yaw(angle):
	print("YAW %.2f degrees"%(angle*180/PI))	
	trans = np.array([[cos(angle),-sin(angle), 0],[sin(angle),cos(angle),0],[0,0,1]])
	print(trans)
	return trans

def clean_matrix(matrix_in):
	mat_out = matrix_in
	rows = np.size(matrix_in, 0)
	cols = np.size(matrix_in, 1)

	for r in range(0,rows):
		for c in range(0,cols):
			mat_out[r,c] = round(matrix_in[r,c], 3)
	return mat_out 

def rotate_around_normal(angle, normal_vec):
	c = cos(angle)
	s = sin(angle)
	C = 1-c
	
	x = normal_vec[0]
	y = normal_vec[1]
	z = normal_vec[2]

	row1 = [x*x*C+c, x*y*C-z*s, x*z*C+y*s]
	row2 = [y*x*C+z*s, y*y*C+c, y*z*C-x*s]
	row3 = [z*x*C-y*s, z*y*C+x*s, z*z*C+c]
	
	trans = np.array([row1, row2, row3])
	print (clean_matrix(trans))
	return trans
def rotate(angle, ground_to_rocket):
	trans = rotate_around_normal(angle, ground_to_rocket[:,Z])
	return trans

def theta(angle, ground_to_rocket):
	trans = yaw(angle)
	return trans

def phi(angle, ground_to_rocket):
	a = ground_to_rocket[0,Y]
	b = ground_to_rocket[1,Y]
	if (abs(a) < 0.0000001 and abs(b) < 0.0000001):
		norm = np.array([0,1,0])
	else:
		norm = np.array([a, b, 0]) #Rocket Z vector crossed with ground Z vector
	norm = norm/np.linalg.norm(norm)
	trans = rotate_around_normal(angle, norm)
	return trans

#def calculate_rocket_angles(r_to_g_trans):


gravity = np.array([0,0,-1])
gravity = gravity.T
thrust = np.array([0,0,1])
thrust = thrust.T
drag = np.array([0,0,-1])
drag = drag.T

static_forces = [gravity]
dynamic_forces = [thrust, drag]

ground_to_rocket = np.eye(3)
rocket_to_ground = np.eye(3)

rocket_angle_rate = np.array([0, -1, 1])
while True:
	print 
	cmd = input("Enter the angle manipulation: ")
	elements = cmd.split(" ")
	action = elements[0]
	angle = float(elements[1])
	angle = angle*PI/180
	transformation = np.eye(3)
	good_cmd = True
	if action == 'r':
		transformation = rotate(angle, ground_to_rocket)
	elif action == 't':
		transformation = theta(angle, ground_to_rocket)
	elif action == 'p':
		transformation = phi(angle, ground_to_rocket)
	else:
		print("Bad command; Interpreted as:\n\tAction: %s\n\tAngle: %f"%(action, angle))
		good_cmd = False
	if (good_cmd):
		ground_to_rocket = np.dot(transformation, ground_to_rocket)
		rocket_to_ground = np.dot(rocket_to_ground, transformation.T)
		
		print("Ground-to-Rocket Matrix (Z is direction of Rocket)")
		print(clean_matrix(ground_to_rocket))
		print("Rocket-to-Ground Matrix (Inverse to Rocket)")
		print(clean_matrix(rocket_to_ground))
		
		print("G-R and R-G multiplied")
		print(clean_matrix(np.dot(ground_to_rocket, rocket_to_ground)))

		forces = np.array([0,0,0])
		forces = forces.T
		thrust = ground_to_rocket[:,2]
		print(thrust)
		drag = -ground_to_rocket[:,2]
		print(drag)
		print(gravity)
		forces = np.add(thrust, drag)
		forces = np.add(forces, gravity)
		print(forces)

		IMU_reading = np.dot(ground_to_rocket, forces)
		print("IMU reading with static and dynamic forces")
		print(IMU_reading)

		
		x_list = []
		y_list = []
		z_list = []
		x_test = []
		y_test = []
		z_test = []
		forces_x_list = []
		forces_y_list = []
		forces_z_list = []
		
		res = 10
		for i in range(1,res+1):
			forces_x_list.append(i*thrust[0]*0.9/res)
			forces_y_list.append(i*thrust[1]*0.9/res)
			forces_z_list.append(i*thrust[2]*0.9/res)
			
			forces_x_list.append(i*drag[0]*0.9/res)
			forces_y_list.append(i*drag[1]*0.9/res)
			forces_z_list.append(i*drag[2]*0.9/res)
			
			forces_x_list.append(i*gravity[0]*0.9/res)
			forces_y_list.append(i*gravity[1]*0.9/res)
			forces_z_list.append(i*gravity[2]*0.9/res)
			
			for axe in range(0,3):
				x_list.append(i*ground_to_rocket[0,axe]/res)
				y_list.append(i*ground_to_rocket[1,axe]/res)
				z_list.append(i*ground_to_rocket[2,axe]/res)
				
				if axe == 0:
					x_test.append(i*0.95/res)
					y_test.append(0)
					z_test.append(0)
				if axe == 1:
					x_test.append(0)
					y_test.append(i*0.95/res)
					z_test.append(0)
				if axe == 2:
					x_test.append(0)
					y_test.append(0)
					z_test.append(i*0.95/res)

		fig = plt.figure()
		ax = fig.add_subplot(111, projection='3d')
		ax.scatter(x_list, y_list, z_list, c='r', marker='o')
		ax.scatter(x_test, y_test, z_test, c='b', marker='o')
		ax.scatter(forces_x_list, forces_y_list, forces_z_list, c='g', marker='o')
		ax.set_xlabel('X (m)')
		ax.set_ylabel('Y (m)')
		ax.set_zlabel('Z (m)')
		ax.set_xlim3d(-1.0, 1.0)
		ax.set_ylim3d(-1.0, 1.0)
		ax.set_zlim3d(-1.0, 1.0)
		plt.show()