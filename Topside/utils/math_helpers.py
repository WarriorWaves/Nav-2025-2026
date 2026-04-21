import sys
import os
import numpy as np

_TOPSIDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if _TOPSIDE not in sys.path:
    sys.path.insert(0, _TOPSIDE)

from config import (
    MIXING_MATRIX, THRUSTER_ORDER,
    THRUSTER_NEUTRAL, THRUSTER_MIN, THRUSTER_MAX,
    AXIS_DEADZONE,
)


def constrain(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def apply_deadzone(value, zone=AXIS_DEADZONE):
    if abs(value) < zone:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - zone) / (1.0 - zone)


def compute_thruster_outputs(surge=0.0, sway=0.0, heave=0.0, yaw=0.0):
    surge = apply_deadzone(surge)
    sway  = apply_deadzone(sway)
    heave = apply_deadzone(heave)
    yaw   = apply_deadzone(yaw)
    input_vec = np.array([surge, sway, heave, yaw])
    outputs   = MIXING_MATRIX @ input_vec
    pwm = [
        int(constrain(THRUSTER_NEUTRAL + val * 150, THRUSTER_MIN, THRUSTER_MAX))
        for val in outputs
    ]
    return dict(zip(THRUSTER_ORDER, pwm))