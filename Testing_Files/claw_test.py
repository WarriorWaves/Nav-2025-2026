import sys
import os
import time
import pygame
import serial

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Topside.config import ROV_PORT, BAUD_RATE

CLAW_OPEN   = 180
CLAW_CLOSED = 0
ROLL_MIN    = 0
ROLL_MAX    = 180
ROLL_CENTRE = 90

CLAW_SPEED        = 2.0
ROLL_SPEED        = 1.5
POLL_MS           = 30
TRIGGER_THRESHOLD = 0.15

AXIS_L2  = 4
AXIS_R2  = 5
BTN_L1   = 9
BTN_R1   = 10
BTN_CROSS   = 0
BTN_SQUARE  = 2


def send_claw(ser, angle):
    angle = max(CLAW_CLOSED, min(CLAW_OPEN, int(angle)))
    ser.write(f"claw:{angle}\n".encode())

def send_roll(ser, angle):
    angle = max(ROLL_MIN, min(ROLL_MAX, int(angle)))
    ser.write(f"roll:{angle}\n".encode())


def self_test(ser):
    print("\n[SELF-TEST] Starting...")
    time.sleep(0.2)
    print("[SELF-TEST] Opening claw (180°)...")
    for a in range(0, CLAW_OPEN + 1, 3):
        send_claw(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)
    print("[SELF-TEST] Closing claw (0°)...")
    for a in range(CLAW_OPEN, CLAW_CLOSED - 1, -3):
        send_claw(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)
    print("[SELF-TEST] Returning claw to open (180°)...")
    for a in range(CLAW_CLOSED, CLAW_OPEN + 1, 3):
        send_claw(ser, a)
        time.sleep(0.02)
    time.sleep(0.3)
    print("[SELF-TEST] Rolling left to 0°...")
    for a in range(ROLL_CENTRE, ROLL_MIN - 1, -3):
        send_roll(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)
    print("[SELF-TEST] Rolling right to 180°...")
    for a in range(ROLL_MIN, ROLL_MAX + 1, 3):
        send_roll(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)
    print("[SELF-TEST] Returning roll to centre (90°)...")
    for a in range(ROLL_MAX, ROLL_CENTRE - 1, -3):
        send_roll(ser, a)
        time.sleep(0.02)
    time.sleep(0.3)
    print("[SELF-TEST] Complete.\n")


def main():
    print("=" * 60)
    print("  WARRIOR WAVES — Claw & Roll Servo Test")
    print("=" * 60)
    print(f"\nOpening {ROV_PORT} @ {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(ROV_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        print("  Serial OK.")
    except serial.SerialException as e:
        print(f"\n  ERROR: {e}")
        print("  Run 'ls /dev/cu.*' and update ROV_PORT in config.py")
        sys.exit(1)

    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("  ERROR: No controller detected.")
        ser.close()
        sys.exit(1)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"  Controller: {joystick.get_name()}")
    print("\nType YES to begin: ", end="", flush=True)
    if input().strip().upper() != "YES":
        ser.close()
        pygame.quit()
        sys.exit(0)

    print("\n  L2=close  R2=open  L1=roll left  R1=roll right  Cross=reset  Square=quit\n")
    self_test(ser)

    claw = float(CLAW_OPEN)
    roll = float(ROLL_CENTRE)
    last_claw = -1
    last_roll = -1
    running = True

    while running:
        pygame.event.pump()

        try:
            if joystick.get_button(BTN_SQUARE):
                running = False
                break
        except Exception:
            pass

        try:
            if joystick.get_button(BTN_CROSS):
                claw = float(CLAW_OPEN)
                roll = float(ROLL_CENTRE)
        except Exception:
            pass

        try:
            l2 = (joystick.get_axis(AXIS_L2) + 1.0) / 2.0
            r2 = (joystick.get_axis(AXIS_R2) + 1.0) / 2.0
            if l2 > TRIGGER_THRESHOLD:
                claw = max(CLAW_CLOSED, claw - CLAW_SPEED * l2)
            elif r2 > TRIGGER_THRESHOLD:
                claw = min(CLAW_OPEN,   claw + CLAW_SPEED * r2)
        except Exception:
            pass

        try:
            if joystick.get_button(BTN_L1):
                roll = max(ROLL_MIN, roll - ROLL_SPEED)
            elif joystick.get_button(BTN_R1):
                roll = min(ROLL_MAX, roll + ROLL_SPEED)
        except Exception:
            pass

        ci = int(round(claw))
        ri = int(round(roll))
        changed = False
        if ci != last_claw:
            send_claw(ser, ci)
            last_claw = ci
            changed = True
        if ri != last_roll:
            send_roll(ser, ri)
            last_roll = ri
            changed = True
        if changed:
            print(f"  Claw: {ci:>3}°   Roll: {ri:>3}°")

        pygame.time.delay(POLL_MS)

    print("\nReturning to safe position...")
    send_claw(ser, CLAW_OPEN)
    send_roll(ser, ROLL_CENTRE)
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
            send_claw(ser, CLAW_OPEN)
            send_roll(ser, ROLL_CENTRE)
            ser.close()
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)