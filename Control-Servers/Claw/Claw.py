
import os
import sys
import serial
import pygame
from pygame.locals import *

SERIAL_PORT = '/dev/cu.usbmodem21201' 
BAUD_RATE = 9600
SEND_SERIAL = True
CLAW_CLOSED = 90
CLAW_OPEN = 180
ROLL_MIN = 0
ROLL_MAX = 180

LEFT_TRIGGER = 4
RIGHT_TRIGGER = 5
LEFT_BUMPER = 9
RIGHT_BUMPER = 10
TRIGGER_THRESHOLD = 0.9

# Command timing settings to prevent servo overload
COMMAND_DELAY = 0.1  # 100ms delay between commands (adjust as needed)
SERIAL_DELAY = 10    # 10ms delay after each serial write
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
        self.pitch_position = 90
        self.claw_opened = False
        
        # State tracking to prevent command spam
        self.last_claw_command = None
        self.last_roll_command = None
        self.command_delay = COMMAND_DELAY  # Configurable delay between commands
        self.last_command_time = 0 

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
        print("Running. Use triggers to open/close claw, bumpers to roll, Up/triangle to pitch.")
        print(f"Command delay: {COMMAND_DELAY}s, Serial delay: {SERIAL_DELAY}ms")
        clock = pygame.time.Clock()
        while True:
            self.handle_inputs()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            clock.tick(60)

    def handle_inputs(self):
        current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
        
        # Only process commands if enough time has passed since last command
        if current_time - self.last_command_time < self.command_delay:
            return
            
        left_trigger = self.controller.get_axis(LEFT_TRIGGER)
        right_trigger = self.controller.get_axis(RIGHT_TRIGGER)

        # Claw control with debouncing
        if left_trigger > TRIGGER_THRESHOLD and self.claw_position != CLAW_CLOSED:
            self.adjust_claw(CLAW_CLOSED)
            self.last_command_time = current_time
        elif right_trigger > TRIGGER_THRESHOLD and self.claw_position != CLAW_OPEN:
            self.adjust_claw(CLAW_OPEN)
            self.last_command_time = current_time
            
        # Roll control with debouncing
        if self.controller.get_button(LEFT_BUMPER) and self.roll_position > ROLL_MIN:
            self.rotate_roll(-1)
            self.last_command_time = current_time
        elif self.controller.get_button(RIGHT_BUMPER) and self.roll_position < ROLL_MAX:
            self.rotate_roll(1)
            self.last_command_time = current_time

    def adjust_claw(self, position):
        if self.claw_position != position:
            self.claw_position = position
            self.claw_opened = (position == CLAW_OPEN)
            self.send_servo_command("claw", self.claw_position)
            print(f"Claw set to {self.claw_position} — Claw Opened: {self.claw_opened}")
            

    def rotate_roll(self, direction):
        self.roll_position += direction
        self.roll_position = max(ROLL_MIN, min(ROLL_MAX, self.roll_position))
        self.send_servo_command("roll", round(self.roll_position))
        print(f"Roll moved to {self.roll_position}")
        print(f'Claw stat {self.claw_opened}')

    def send_servo_command(self, servo, position):
        if not SEND_SERIAL:
            return
        command = f"{servo}:{position}\n"
        try:
            if self.arduino:
                self.arduino.write(command.encode('utf-8'))
                # Small delay to prevent overwhelming the Arduino
                pygame.time.delay(SERIAL_DELAY)  # Configurable delay
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