import os
import sys
import serial
import pygame
from pygame.locals import *
import time

SERIAL_PORT = 'COM5' 
BAUD_RATE = 9600
SEND_SERIAL = True

CLAW_CLOSED = 90
CLAW_OPEN = 180
ROLL_MIN = 0
ROLL_MAX = 180
ROLL_SPEED = 1     # degrees per frame
CLAW_SPEED = 1.5   # degrees per frame

LEFT_TRIGGER = 4
RIGHT_TRIGGER = 5
LEFT_BUMPER = 9
RIGHT_BUMPER = 10
TRIGGER_THRESHOLD = 0.9

os.environ.update({
    "SDL_VIDEO_ALLOW_SCREENSAVER": "1",
    "SDL_TRIGGER_ALLOW_BACKGROUND_EVENTS": "1",
    "SDL_HINT_TRIGGER_ALLOW_BACKGROUND_EVENTS": "1",
    "SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR": "0"
})

class MainProgram:
    def __init__(self):
        pygame.init()
        self.arduino = None
        self.controller = None
        self.init_controller()
        self.init_serial()

        self.claw_position = CLAW_CLOSED
        self.roll_position = 90

    def init_controller(self):
        pygame.joystick.init()
        while pygame.joystick.get_count() == 0:
            print("No controllers detected. Please connect a PS5 controller.")
            pygame.time.delay(1000)
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()  
        print(f"Connected to controller: {self.controller.get_name()}")

    def init_serial(self):
        try:
            self.arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"Connected to Arduino on {SERIAL_PORT}")
        except serial.SerialException as e:
            print(f"Could not open serial port {SERIAL_PORT}: {e}")
            self.quit(1)

    def run(self):
        clock = pygame.time.Clock()
        print("Running. Use triggers to open/close claw, bumpers to roll.")

        while True:
            self.handle_inputs()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            clock.tick(60)

    def handle_inputs(self):
        # Read triggers
        left_trigger = self.controller.get_axis(LEFT_TRIGGER)
        right_trigger = self.controller.get_axis(RIGHT_TRIGGER)

        # Determine target claw position
        target_claw = self.claw_position
        if left_trigger > TRIGGER_THRESHOLD:
            target_claw = CLAW_CLOSED 
        elif right_trigger > TRIGGER_THRESHOLD:
            target_claw = CLAW_OPEN

        # Gradually move claw
        if self.claw_position < target_claw:
            self.claw_position = min(self.claw_position + CLAW_SPEED, target_claw)
        elif self.claw_position > target_claw:
            self.claw_position = max(self.claw_position - CLAW_SPEED, target_claw)

        self.send_servo_command("claw", round(self.claw_position))

        # Roll control
        target_roll = self.roll_position
        if self.controller.get_button(LEFT_BUMPER):
            target_roll = max(ROLL_MIN, self.roll_position - ROLL_SPEED)
        elif self.controller.get_button(RIGHT_BUMPER):
            target_roll = min(ROLL_MAX, self.roll_position + ROLL_SPEED)

        self.roll_position = target_roll
        self.send_servo_command("roll", round(self.roll_position))

    def send_servo_command(self, servo, position):
        if not SEND_SERIAL or self.arduino is None:
            return
        command = f"{servo}:{position}\n"
        try:
            self.arduino.write(command.encode('utf-8'))
        except Exception as e:
            print(f"Error sending data to Arduino: {e}")

    def quit(self, status=0):
        print("Exiting...")
        if self.arduino:
            self.arduino.close()
        pygame.quit()
        sys.exit(status)

if __name__ == "__main__":
    program = MainProgram()
    program.run()
