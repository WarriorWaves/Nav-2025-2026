import sys
import os
import time
import pygame
import serial

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Topside'))

from config import ROV_PORT, BAUD_RATE, THRUSTER_ORDER, THRUSTER_NEUTRAL
from utils.math_helpers import compute_thruster_outputs

POLL_MS       = 30
TEST_PWM      = 1550
TEST_DURATION = 3.0
TEST_PAUSE    = 1.0

AXIS_LEFT_X  = 0
AXIS_LEFT_Y  = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
BTN_TRIANGLE = 3
BTN_SQUARE   = 2
BTN_CROSS    = 0
AXIS_DEADZONE = 0.08

THRUSTER_NOTES = {
    "FR": "front-right horizontal — should push water LEFT/BACK",
    "FL": "front-left  horizontal — should push water RIGHT/BACK",
    "BR": "back-right  horizontal — should push water LEFT/FRONT",
    "BL": "back-left   horizontal — should push water RIGHT/FRONT",
    "F":  "front vertical — should push water DOWN",
    "B":  "back  vertical — should push water DOWN",
}

def send_pwm(ser, pwm_list):
    cmd = "THR " + " ".join(str(int(p)) for p in pwm_list) + "\n"
    ser.write(cmd.encode())

def all_neutral(ser):
    send_pwm(ser, [THRUSTER_NEUTRAL] * 6)

def single_thruster(ser, index, pwm):
    values = [THRUSTER_NEUTRAL] * 6
    values[index] = pwm
    send_pwm(ser, values)

def sequential_test(ser, joystick):
    print("\n" + "─" * 60)
    print(" SEQUENTIAL THRUSTER TEST")
    print(" Each thruster spins for 3 s at low power (1550 µs).")
    print(" Watch direction. Press any button to advance.")
    print("─" * 60 + "\n")

    for i, name in enumerate(THRUSTER_ORDER):
        note = THRUSTER_NOTES.get(name, "")
        print(f"  [{i+1}/6] Thruster {name} — {note}")
        print(f"  Spinning in 3 seconds... ", end="", flush=True)
        for countdown in range(3, 0, -1):
            print(f"{countdown}... ", end="", flush=True)
            time.sleep(1.0)
        print("GO")
        single_thruster(ser, i, TEST_PWM)
        time.sleep(TEST_DURATION)
        all_neutral(ser)
        print(f"  STOPPED. Press any button to continue...")
        _wait_for_any_button(joystick)
        print(f"  ✓ {name} done.\n")

    print("  Sequential test complete.\n")

def _wait_for_any_button(joystick):
    while True:
        pygame.event.pump()
        if not any(joystick.get_button(b) for b in range(joystick.get_numbuttons())):
            break
        pygame.time.delay(50)
    while True:
        pygame.event.pump()
        if any(joystick.get_button(b) for b in range(joystick.get_numbuttons())):
            break
        pygame.time.delay(50)

def main():
    print("=" * 60)
    print(" WARRIOR WAVES — Thruster Test (OUT OF WATER ONLY)")
    print("=" * 60)
    print(f"\nOpening serial port: {ROV_PORT} @ {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(ROV_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        all_neutral(ser)
        print("  Serial OK. Neutral sent — waiting for ESC arming beeps (2–3 s)...")
        time.sleep(3)
        print("  ESCs should have beeped. If not, check power and re-run.")
    except serial.SerialException as e:
        print(f"\n  ERROR: Could not open {ROV_PORT}: {e}")
        print("  Run 'ls /dev/cu.*' to find the correct port and update config.py.")
        sys.exit(1)

    print("\nInitialising pygame and DualSense controller...")
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("  ERROR: No Bluetooth controller detected.")
        all_neutral(ser)
        ser.close()
        sys.exit(1)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"  Controller OK: {joystick.get_name()}")

    print("\n" + "─" * 60)
    print(" CONTROLS:")
    print("  Left stick X/Y  -> sway / surge")
    print("  Right stick Y   ->heave (up/down)")
    print("  Right stick X   ->yaw   (rotation)")
    print("  Triangle        -> run automatic sequential test")
    print("  Square          -> EMERGENCY STOP (all -> 1500 immediately)")
    print("  Cross (X)       -> quit safely")
    print("─" * 60)
    print("\nLive manual control active. All thrusters at neutral.\n")

    estopped = False
    running  = True

    while running:
        pygame.event.pump()

        try:
            if joystick.get_button(BTN_SQUARE):
                if not estopped:
                    all_neutral(ser)
                    estopped = True
                    print("\n  *** ESTOP *** All thrusters -> 1500. Press any other button to resume.\n")
                pygame.time.delay(POLL_MS)
                continue
            elif estopped:
                if any(joystick.get_button(b)
                       for b in range(joystick.get_numbuttons())
                       if b != BTN_SQUARE):
                    estopped = False
                    print("  ESTOP cleared. Manual control resumed.\n")
                pygame.time.delay(POLL_MS)
                continue
        except Exception:
            pass

        try:
            if joystick.get_button(BTN_CROSS):
                print("\n[QUIT] Cross pressed.")
                running = False
                break
        except Exception:
            pass

        try:
            if joystick.get_button(BTN_TRIANGLE):
                all_neutral(ser)
                time.sleep(0.5)
                sequential_test(ser, joystick)
                print("Resuming manual control.\n")
                pygame.time.delay(POLL_MS)
                continue
        except Exception:
            pass

        def axis(idx):
            try:
                v = joystick.get_axis(idx)
                return v if abs(v) >= AXIS_DEADZONE else 0.0
            except Exception:
                return 0.0

        surge = axis(AXIS_LEFT_Y)  * -1
        sway  = axis(AXIS_LEFT_X)
        heave = axis(AXIS_RIGHT_Y) * -1
        yaw   = axis(AXIS_RIGHT_X)

        pwm_dict = compute_thruster_outputs(surge, sway, heave, yaw)
        pwm_list = [pwm_dict[n] for n in THRUSTER_ORDER]
        send_pwm(ser, pwm_list)

        labels = " ".join(f"{n}:{v}" for n, v in zip(THRUSTER_ORDER, pwm_list))
        print(f"\r  {labels} ", end="", flush=True)
        pygame.time.delay(POLL_MS)

    print("\n\nSending neutral to all thrusters and closing...")
    all_neutral(ser)
    time.sleep(0.3)
    ser.close()
    pygame.quit()
    print("Done. Test complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Ctrl+C] Interrupted. Sending neutral to all thrusters...")
        try:
            ser = serial.Serial(ROV_PORT, BAUD_RATE, timeout=1)
            time.sleep(1)
            all_neutral(ser)
            ser.close()
            print("All thrusters → neutral.")
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)