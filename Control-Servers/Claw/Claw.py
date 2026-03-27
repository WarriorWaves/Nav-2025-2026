import os
import sys
import serial
import pygame
import time

SERIAL_PORT = "/dev/cu.usbmodem2017_2_251"
SERIAL_PORT = 'COM5'
BAUD_RATE = 9600
SEND_SERIAL = True

CLAW_CLOSED = 0
CLAW_OPEN = 180
ROLL_MIN = 0
ROLL_MAX = 180


ROLL_SPEED = 1
CLAW_SPEED = 1.5

LEFT_TRIGGER = 4
RIGHT_TRIGGER = 5
LEFT_BUMPER = 9
RIGHT_BUMPER = 10

TRIGGER_THRESHOLD = 0.9

class MainProgram:
    def __init__(self):
        pygame.init()
        self.arduino = None
        self.controller = None

        self.init_controller()
        self.init_serial()

        self.claw_position = CLAW_OPEN
        self.roll_position = 90
        self.last_claw_sent = round(self.claw_position)
        self.last_roll_sent = round(self.roll_position)

    def init_controller(self):
        pygame.joystick.init()
        while pygame.joystick.get_count() == 0:
            print("Connect PS5 controller...")
            pygame.time.delay(1000)

        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

        print(f"Connected to {self.controller.get_name()}")

    def init_serial(self):
        try:
            self.arduino = serial.Serial(
                SERIAL_PORT,
                BAUD_RATE,
                timeout=1,
                write_timeout=1
            )
            print(f"Connected to Arduino on {SERIAL_PORT}")
            time.sleep(2)
            self.arduino.reset_input_buffer()

        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.quit(1)

    def run(self):
        clock = pygame.time.Clock()
        print("Triggers = claw | Bumpers = roll")

        while True:
            self.handle_inputs()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

            clock.tick(60)

    def handle_inputs(self):
        left_trigger = self.controller.get_axis(LEFT_TRIGGER)
        right_trigger = self.controller.get_axis(RIGHT_TRIGGER)


        # Determine claw target
        target_claw = self.claw_position

        if left_trigger > TRIGGER_THRESHOLD:
            target_claw = CLAW_CLOSED
        elif right_trigger > TRIGGER_THRESHOLD:
            target_claw = CLAW_OPEN


        # Smooth movement
        if self.claw_position < target_claw:
            self.claw_position = min(self.claw_position + CLAW_SPEED, target_claw)
        elif self.claw_position > target_claw:
            self.claw_position = max(self.claw_position - CLAW_SPEED, target_claw)


        # Roll control
        target_roll = self.roll_position
        if self.controller.get_button(LEFT_BUMPER):
            target_roll = max(ROLL_MIN, self.roll_position - ROLL_SPEED)
        elif self.controller.get_button(RIGHT_BUMPER):
            target_roll = min(ROLL_MAX, self.roll_position + ROLL_SPEED)

        self.roll_position = target_roll

        # --- Serial Send Logic (Fixed Spam) ---
        claw_pos_rounded = round(self.claw_position)
        if claw_pos_rounded != self.last_claw_sent:
            self.send_servo_command("claw", claw_pos_rounded)
            self.last_claw_sent = claw_pos_rounded

        roll_pos_rounded = round(self.roll_position)
        if roll_pos_rounded != self.last_roll_sent:
            self.send_servo_command("roll", roll_pos_rounded)
            self.last_roll_sent = roll_pos_rounded

    def send_servo_command(self, servo, position):
        if not SEND_SERIAL or self.arduino is None:
            return

        command = f"{servo}:{position}\n"
        try:
            self.arduino.write(command.encode())
        except Exception as e:
            print("Serial write error:", e)

    def quit(self, status=0):
        print("Exiting...")
        if self.arduino:
            self.arduino.close()
        pygame.quit()
        sys.exit(status)

if __name__ == "__main__":
    program = MainProgram()
    program.run()