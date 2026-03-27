import serial
import pygame
import time
import sys

# Change to your specific COM/tty port
SERIAL_PORT = 'COM5'
BAUD_RATE = 9600

# PS5 Axis Mapping
LEFT_STICK_Y = 1   # Surge (Forward/Back)
RIGHT_STICK_Y = 3  # Heave (Up/Down)
DEADZONE = 0.1

def map_axis_to_pwm(axis_val):
    # Ignore stick drift
    if abs(axis_val) < DEADZONE:
        return 1500
    # Map -1.0 to 1.0 -> 1350 to 1650 (safe limits)
    return int(1500 + (axis_val * 150))

def run_thruster_test():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("Please connect a PS5 Controller.")
        sys.exit()
        
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2) # Wait for Arduino reset
        print("Connected to Thruster Arduino.")
    except serial.SerialException:
        print("Failed to connect to Serial Port.")
        sys.exit()

    clock = pygame.time.Clock()
    print("Test Active. Left Stick = Surge, Right Stick = Heave.")
    print("Press CTRL+C to stop.")

    try:
        while True:
            pygame.event.pump()
            
            surge_axis = -joystick.get_axis(LEFT_STICK_Y) # Invert so up is forward
            heave_axis = -joystick.get_axis(RIGHT_STICK_Y)
            
            surge_pwm = map_axis_to_pwm(surge_axis)
            heave_pwm = map_axis_to_pwm(heave_axis)
            
            # Mapping: [FR, FL, BR, BL, F, B]
            # Applying surge to the 4 horizontal thrusters, heave to the 2 verticals
            pwm_list = [surge_pwm, surge_pwm, surge_pwm, surge_pwm, heave_pwm, heave_pwm]
            
            command = "THR " + " ".join(str(p) for p in pwm_list) + "\n"
            arduino.write(command.encode())
            
            clock.tick(20) # 20 Hz update rate to prevent serial flooding
            
    except KeyboardInterrupt:
        print("\nStopping Thrusters...")
        # Send kill signal
        arduino.write(b"THR 1500 1500 1500 1500 1500 1500\n")
        arduino.close()
        pygame.quit()

if __name__ == "__main__":
    run_thruster_test()