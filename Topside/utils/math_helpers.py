import math
import numpy as np

def constrain(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def map_range(value, from_min, from_max, to_min, to_max):
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

THRUSTERS = ["FR", "FL", "BR", "BL", "F", "B"]
DOF = ["surge", "sway", "heave", "yaw"]

MIXING_MATRIX = np.array([
    [ 1, -1, 0, -1],
    [ 1,  1, 0,  1],
    [ 1,  1, 0, -1],
    [ 1, -1, 0,  1],
    [ 0,  0, 1,  0],
    [ 0,  0, 1,  0],
])

def compute_thruster_outputs(surge=0.0, sway=0.0, heave=0.0, yaw=0.0):
    input_vector = np.array([surge, sway, heave, yaw])
    outputs = MIXING_MATRIX @ input_vector
    pwm = [int(1500 + val * 150) for val in outputs]
    pwm = [constrain(x, 1350, 1650) for x in pwm]
    return dict(zip(THRUSTERS, pwm))
