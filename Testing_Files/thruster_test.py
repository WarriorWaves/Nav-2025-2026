import sys
import os
import time
import pygame
import serial


_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Topside.config import ROV_PORT, BAUD_RATE, THRUSTER_ORDER, THRUSTER_NEUTRAL
from Topside.utils.math_helpers import compute_thruster_outputs

POLL_MS       = 30
TEST_PWM      = 1550
TEST_DURATION = 3.0
AXIS_DEADZONE = 0.08

AXIS_LEFT_X  = 0
AXIS_LEFT_Y  = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
BTN_TRIANGLE = 3
BTN_SQUARE   = 2
BTN_CROSS    = 0

THRUSTER_NOTES = {
    "FR": "front-right horizontal — pushes water LEFT  and BACK",
    "FL": "front-left  horizontal — pushes water RIGHT and BACK",
    "BR": "back-right  horizontal — pushes water LEFT  and FRONT",
    "BL": "back-left   horizontal — pushes water RIGHT and FRONT",
    "F":  "front vertical         — pushes water DOWN",
    "B":  "back  vertical         — pushes water DOWN",
}


def send_pwm(ser, pwm_list):
    ser.write(("THR " + " ".join(str(int(p)) for p in pwm_list) + "\n").encode())

def all_neutral(ser):
    send_pwm(ser, [THRUSTER_NEUTRAL] * 6)

def single_thruster(ser, index, pwm):
    values = [THRUSTER_NEUTRAL] * 6
    values[index] = pwm
    send_pwm(ser, values)


def sequential_test(ser, joystick):
    print("\n" + "─" * 60)
    print("  SEQUENTIAL THRUSTER TEST")
    print("  Each thruster spins 3s at low power. Press any button to advance.")
    print("─" * 60 + "\n")

    for i, name in enumerate(THRUSTER_ORDER):
        print(f"  [{i+1}/6] {name}  —  {THRUSTER_NOTES.get(name, '')}")
        print("  Spinning in: ", end="", flush=True)
        for c in range(3, 0, -1):
            print(f"{c}... ", end="", flush=True)
            time.sleep(1.0)
        print("GO")
        single_thruster(ser, i, TEST_PWM)
        time.sleep(TEST_DURATION)
        all_neutral(ser)
        print("  STOPPED — press any button to continue...")
        _wait_button(joystick)
        print(f"  ✓ {name} done.\n")

    print("  Sequential test complete.\n")


def _wait_button(joystick):
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
    print("  WARRIOR WAVES — Thruster Test  (OUT OF WATER ONLY)")
    print("=" * 60)
    print(f"\nOpening {ROV_PORT} @ {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(ROV_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        all_neutral(ser)
        print("  Serial OK. Waiting for ESC arming beeps...")
        time.sleep(3)
    except serial.SerialException as e:
        print(f"\n  ERROR: {e}")
        print("  Run 'ls /dev/cu.*' and update ROV_PORT in config.py")
        sys.exit(1)

    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("  ERROR: No controller detected.")
        all_neutral(ser)
        ser.close()
        sys.exit(1)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"  Controller: {joystick.get_name()}")
    print("\n  Left stick X/Y = sway/surge | Right stick Y = heave | Right stick X = yaw")
    print("  Triangle = sequential test | Square = ESTOP | Cross = quit\n")

    estopped = False
    running  = True

    while running:
        pygame.event.pump()

        try:
            if joystick.get_button(BTN_SQUARE):
                if not estopped:
                    all_neutral(ser)
                    estopped = True
                    print("\n  *** ESTOP *** Press any other button to resume.\n")
                pygame.time.delay(POLL_MS)
                continue
            elif estopped:
                if any(joystick.get_button(b) for b in range(joystick.get_numbuttons()) if b != BTN_SQUARE):
                    estopped = False
                    print("  ESTOP cleared.\n")
                pygame.time.delay(POLL_MS)
                continue
        except Exception:
            pass

        try:
            if joystick.get_button(BTN_CROSS):
                running = False
                break
        except Exception:
            pass

        try:
            if joystick.get_button(BTN_TRIANGLE):
                all_neutral(ser)
                time.sleep(0.5)
                sequential_test(ser, joystick)
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

        pwm_dict = compute_thruster_outputs(
            surge = axis(AXIS_LEFT_Y)  * -1,
            sway  = axis(AXIS_LEFT_X),
            heave = axis(AXIS_RIGHT_Y) * -1,
            yaw   = axis(AXIS_RIGHT_X),
        )
        pwm_list = [pwm_dict[n] for n in THRUSTER_ORDER]
        send_pwm(ser, pwm_list)
        print(f"\r  " + " ".join(f"{n}:{v}" for n, v in zip(THRUSTER_ORDER, pwm_list)), end="", flush=True)
        pygame.time.delay(POLL_MS)

    print("\n\nSending neutral and closing...")
    all_neutral(ser)
    time.sleep(0.3)
    ser.close()
    pygame.quit()
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Ctrl+C]")
        try:
            ser = serial.Serial(ROV_PORT, BAUD_RATE, timeout=1)
            time.sleep(1)
            all_neutral(ser)
            ser.close()
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)