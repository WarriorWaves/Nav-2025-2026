import serial
import time

THRUSTER_ORDER = ["FR", "FL", "BR", "BL", "F", "B"]

class ThrusterController:
    def __init__(self, port="/dev/ttyUSB0", baud=9600):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        time.sleep(2)  # Arduino reset delay

    def send_pwm_list(self, pwm_list):
        """
        pwm_list: [FR, FL, BR, BL, F, B]
        """
        if len(pwm_list) != 6:
            raise ValueError("Expected 6 PWM values")

        cmd = "THR " + " ".join(str(int(p)) for p in pwm_list) + "\n"
        self.ser.write(cmd.encode())

    def send_from_mapping(self, pwm_dict):
        """
        pwm_dict: output from compute_thruster_outputs()
        """
        pwm_list = [pwm_dict[name] for name in THRUSTER_ORDER]
        self.send_pwm_list(pwm_list)
