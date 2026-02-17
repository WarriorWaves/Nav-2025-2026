import serial
import time

class CameraServo:
    def __init__(self, port="/dev/ttyUSB2", baud=9600):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        time.sleep(2)  # allow Arduino reset

    def tilt(self, angle):
        """
        angle: 0–180 degrees
        """
        angle = max(0, min(180, int(angle)))
        cmd = f"tilt:{angle}\n"
        self.ser.write(cmd.encode())
