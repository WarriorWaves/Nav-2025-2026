import numpy as np

THRUSTERS = ["FR", "FL", "BR", "BL", "F", "B"]

# Degrees of freedom: surge (X), sway (Y), heave (Z), yaw (rotation around Z)
DOF = ["surge", "sway", "heave", "yaw"]

# Mixing matrix: rows = thrusters, columns = DOFs
# Order of DOFs = [surge, sway, heave, yaw]
MIXING_MATRIX = np.array([
    [ 1, -1, 0, -1],  # FR (front right)
    [ 1,  1, 0,  1],  # FL (front left)
    [ 1,  1, 0, -1],  # BR (back right)
    [ 1, -1, 0,  1],  # BL (back left)
    [ 0,  0, 1,  0],  # F (vertical)
    [ 0,  0, 1,  0],  # B (vertical)
])

def compute_thruster_outputs(surge=0.0, sway=0.0, heave=0.0, yaw=0.0):

    input_vector = np.array([surge, sway, heave, yaw])

    outputs = MIXING_MATRIX @ input_vector
    pwm = [int(1500 + val * 150) for val in outputs]
    pwm = [min(max(x, 1350), 1650) for x in pwm]
    return dict(zip(THRUSTERS, pwm))

if __name__ == "__main__":
    thrusters = compute_thruster_outputs(surge=1.0, yaw=0.3)
    print("Thruster outputs:")
    for t, val in thrusters.items():
        print(f" {t}: {val}")
