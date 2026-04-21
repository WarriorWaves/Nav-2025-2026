import sys
import os
import time
import pygame
import serial


_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Topside.config import ROV_PORT, BAUD_RATE

TILT_MIN  = 0
TILT_MAX  = 180
TILT_STEP = 2.0
POLL_MS   = 30

HAT_UP     = (0,  1)
HAT_DOWN   = (0, -1)
BTN_CROSS  = 0
BTN_SQUARE = 2


def send_tilt(ser, angle):
    angle = max(TILT_MIN, min(TILT_MAX, int(angle)))
    ser.write(f"tilt:{angle}\n".encode())


def sweep(ser):
    print("\n[SELF-TEST] 90 -> 180 -> 0 -> 90")
    for a in range(90, 181, 2):
        send_tilt(ser, a)
        time.sleep(0.02)
    print("[SELF-TEST] 180 reached")
    time.sleep(0.3)
    for a in range(180, -1, -2):
        send_tilt(ser, a)
        time.sleep(0.02)
    print("[SELF-TEST] 0 reached")
    time.sleep(0.3)
    for a in range(0, 91, 2):
        send_tilt(ser, a)
        time.sleep(0.02)
    print("[SELF-TEST] 90 reached. Complete.\n")


def main():
    print("=" * 60)
    print("  WARRIOR WAVES — Camera Servo Tilt Test")
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

    print("\n  D-pad UP=tilt up  D-pad DOWN=tilt down  Cross=centre  Square=quit\n")
    sweep(ser)

    tilt         = 90.0
    last_printed = -1
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
                tilt = 90.0
        except Exception:
            pass

        try:
            hat = joystick.get_hat(0)
            if hat == HAT_UP:
                tilt = min(TILT_MAX, tilt + TILT_STEP)
            elif hat == HAT_DOWN:
                tilt = max(TILT_MIN, tilt - TILT_STEP)
        except Exception:
            pass

        ai = int(round(tilt))
        if ai != last_printed:
            send_tilt(ser, ai)
            print(f"  Tilt: {ai:>3}°")
            last_printed = ai

        pygame.time.delay(POLL_MS)

    print("\nReturning to 90° and closing...")
    send_tilt(ser, 90)
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
            send_tilt(ser, 90)
            ser.close()
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)