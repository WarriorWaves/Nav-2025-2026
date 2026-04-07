import sys
import os
import time
import pygame
import serial

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Topside'))

from config import ROV_PORT, BAUD_RATE

CLAW_OPEN    = 180
CLAW_CLOSED  = 0
ROLL_MIN     = 0
ROLL_MAX     = 180
ROLL_CENTRE  = 90

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

def send_claw(ser, angle: int):
    angle = max(CLAW_CLOSED, min(CLAW_OPEN, int(angle)))
    ser.write(f"claw:{angle}\n".encode())

def send_roll(ser, angle: int):
    angle = max(ROLL_MIN, min(ROLL_MAX, int(angle)))
    ser.write(f"roll:{angle}\n".encode())

def self_test(ser):
    print("\n[SELF-TEST] Starting claw and roll self-test...")
    time.sleep(0.2)

    print("[SELF-TEST] → Opening claw fully (180°)...")
    for a in range(0, CLAW_OPEN + 1, 3):
        send_claw(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)

    print("[SELF-TEST] → Closing claw fully (0°)...")
    for a in range(CLAW_OPEN, CLAW_CLOSED - 1, -3):
        send_claw(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)

    print("[SELF-TEST] → Returning claw to open (180°)...")
    for a in range(CLAW_CLOSED, CLAW_OPEN + 1, 3):
        send_claw(ser, a)
        time.sleep(0.02)
    time.sleep(0.3)

    print("[SELF-TEST] → Rolling left to 0°...")
    for a in range(ROLL_CENTRE, ROLL_MIN - 1, -3):
        send_roll(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)

    print("[SELF-TEST] → Rolling right to 180°...")
    for a in range(ROLL_MIN, ROLL_MAX + 1, 3):
        send_roll(ser, a)
        time.sleep(0.02)
    time.sleep(1.0)

    print("[SELF-TEST] → Returning roll to centre (90°)...")
    for a in range(ROLL_MAX, ROLL_CENTRE - 1, -3):
        send_roll(ser, a)
        time.sleep(0.02)
    time.sleep(0.3)

    print("[SELF-TEST] Complete. Claw open, roll centred.\n")

def main():
    print("=" * 60)
    print(" WARRIOR WAVES — Claw & Roll Servo Test")
    print("=" * 60)

    print(f"\nOpening serial port: {ROV_PORT} @ {BAUD_RATE} baud...")
    try:
        ser = serial.Serial(ROV_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        print("  Serial OK.")
    except serial.SerialException as e:
        print(f"\n  ERROR: Could not open {ROV_PORT}: {e}")
        print("  Run 'ls /dev/cu.*' to find the correct port and update config.py.")
        sys.exit(1)

    print("\nInitialising pygame and DualSense controller...")
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("  ERROR: No Bluetooth controller detected.")
        ser.close()
        sys.exit(1)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"  Controller OK: {joystick.get_name()}")

    print("\n" + "=" * 60)
    print(" CONNECTIONS CONFIRMED:")
    print(f"  Serial     : {ROV_PORT}")
    print(f"  Controller : {joystick.get_name()}")
    print("=" * 60)
    print("\nType YES and press Enter to begin: ", end="", flush=True)
    if input().strip().upper() != "YES":
        print("Aborted.")
        ser.close()
        pygame.quit()
        sys.exit(0)

    print("\n" + "─" * 60)
    print(" CONTROLS:")
    print("  L2 (hold)  → close claw (proportional to trigger)")
    print("  R2 (hold)  → open  claw (proportional to trigger)")
    print("  L1         → roll left")
    print("  R1         → roll right")
    print("  Cross (X)  → reset: claw open (180°), roll centre (90°)")
    print("  Square     → quit test safely")
    print("─" * 60)

    self_test(ser)

    claw = float(CLAW_OPEN)
    roll = float(ROLL_CENTRE)
    last_claw_sent = -1
    last_roll_sent = -1

    print("Live control active. Press Square to quit.\n")
    running = True

    while running:
        pygame.event.pump()

        try:
            if joystick.get_button(BTN_SQUARE):
                print("\n[QUIT] Square pressed.")
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

        claw_int = int(round(claw))
        roll_int = int(round(roll))
        changed  = False

        if claw_int != last_claw_sent:
            send_claw(ser, claw_int)
            last_claw_sent = claw_int
            changed = True
        if roll_int != last_roll_sent:
            send_roll(ser, roll_int)
            last_roll_sent = roll_int
            changed = True
        if changed:
            print(f"  Claw: {claw_int:>3}°  Roll: {roll_int:>3}°")

        pygame.time.delay(POLL_MS)

    print("\nReturning to safe position: claw open (180°), roll centre (90°)...")
    send_claw(ser, CLAW_OPEN)
    send_roll(ser, ROLL_CENTRE)
    time.sleep(0.3)
    ser.close()
    pygame.quit()
    print("Done. Test complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Ctrl+C] Interrupted. Attempting safe exit...")
        try:
            ser = serial.Serial(ROV_PORT, BAUD_RATE, timeout=1)
            time.sleep(1)
            send_claw(ser, CLAW_OPEN)
            send_roll(ser, ROLL_CENTRE)
            ser.close()
            print("Claw and roll returned to safe position.")
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)