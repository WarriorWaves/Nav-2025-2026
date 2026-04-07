
import numpy as np
import sys
import os

# Allow import whether called from Topside/ or Testing_Files/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    MIXING_MATRIX, THRUSTER_ORDER,
    THRUSTER_NEUTRAL, THRUSTER_MIN, THRUSTER_MAX,
    AXIS_DEADZONE,
)


def constrain(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def map_range(value, from_min, from_max, to_min, to_max):
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min


def apply_deadzone(value: float, zone: float = AXIS_DEADZONE) -> float:
    if abs(value) < zone:
        return 0.0
    sign = 1 if value > 0 else -1
    return sign * (abs(value) - zone) / (1.0 - zone)


def compute_thruster_outputs(surge=0.0, sway=0.0, heave=0.0, yaw=0.0):
    surge = apply_deadzone(surge)
    sway  = apply_deadzone(sway)
    heave = apply_deadzone(heave)
    yaw   = apply_deadzone(yaw)

    input_vec = np.array([surge, sway, heave, yaw])
    outputs   = MIXING_MATRIX @ input_vec

    pwm = [
        int(constrain(int(THRUSTER_NEUTRAL + val * 150), THRUSTER_MIN, THRUSTER_MAX))
        for val in outputs
    ]
    return dict(zip(THRUSTER_ORDER, pwm))
