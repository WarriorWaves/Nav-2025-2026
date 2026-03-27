import serial
import pygame
import time
import sys

SERIAL_PORT = 'COM5'
BAUD_RATE = 9600
TILT_SPEED = 2

def run_camera_test():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("Please connect a PS5 Controller.")
        sys.exit()
        
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)
    except serial.SerialException:
        print("Failed to connect to Serial Port.")
        sys.exit()

    clock = pygame.time.Clock()
    angle = 90 # Start centered
    last_angle = 90

    print("Test Active. Use D-Pad UP/DOWN to tilt camera.")
    
    try:
        while True:
            pygame.event.pump()
            
            # D-pad returns a tuple (x, y). y is 1 for Up, -1 for Down.
            dpad_y = joystick.get_hat(0)[1] 
            
            if dpad_y == 1:
                angle = min(180, angle + TILT_SPEED)
            elif dpad_y == -1:
                angle = max(0, angle - TILT_SPEED)
                
            if angle != last_angle:
                command = f"tilt:{angle}\n"
                arduino.write(command.encode())
                last_angle = angle
                print(f"Camera Angle: {angle}")
                
            clock.tick(30)
            
    except KeyboardInterrupt:
        print("\nExiting Camera Test...")
        arduino.close()
        pygame.quit()

if __name__ == "__main__":
    run_camera_test()