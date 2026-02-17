import serial
import time

def open_serial(port, baudrate=9600, timeout=1):
    ser = serial.Serial(port, baudrate, timeout=timeout)
    time.sleep(2)
    return ser

def send_command(ser, command):
    if ser and ser.is_open:
        ser.write(f"{command}\n".encode())
        time.sleep(0.01)

def read_line(ser):
    if ser and ser.in_waiting > 0:
        return ser.readline().decode().strip()
    return None
