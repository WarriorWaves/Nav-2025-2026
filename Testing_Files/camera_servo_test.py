import sys
import time
import pygame
import serial
from config import CAMERA_SERVO_PORT, BAUD_RATE


TILT_MIN   = 0
TILT_MAX   = 180
TILT_STEP  = 2.0     
POLL_MS    = 30      

HAT_UP     = (0,  1)
HAT_DOWN   = (0, -1)
BTN_CROSS  = 0
BTN_SQUARE = 2


#Serial helpers
def send_tilt(ser, angle: int):
    angle = max(TILT_MIN, min(TILT_MAX, int(angle)))
    ser.write(f"tilt:{angle}\n".encode())


def sweep(ser, steps=None):
    """Startup self-test: 90 → 180 → 0 → 90."""
    print("\n[SELF-TEST] Sweeping: 90° → 180° → 0° → 90°")
    for angle in range(90, 181, 2):
        send_tilt(ser, angle)
        time.sleep(0.02)
    print("[SELF-TEST]  → 180° reached")
    time.sleep(0.3)
    for angle in range(180, -1, -2):
        send_tilt(ser, angle)
        time.sleep(0.02)
    print("[SELF-TEST]  → 0° reached")
    time.sleep(0.3)
    for angle in range(0, 91, 2):
        send_tilt(ser, angle)
        time.sleep(0.02)
    print("[SELF-TEST]  → 90° reached. Self-test complete.\n")



def main():
    
    print("=" * 60)
    print("  WARRIOR WAVES — Camera Servo Test")
    print("=" * 60)
    print(f"\nOpening serial port: {CAMERA_SERVO_PORT} @ {BAUD_RATE} baud...")
    try:
        ser = serial.Serial(CAMERA_SERVO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        print("  Serial OK.")
    except serial.SerialException as e:
        print(f"\n  ERROR: Could not open {CAMERA_SERVO_PORT}: {e}")
        print("  Run 'ls /dev/cu.*' to find the correct port and update config.py.")
        sys.exit(1)

    # Pygame / controller added
    print("\nInitialising pygame and DualSense controller...")
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("  ERROR: No Bluetooth controller detected.")
        print("  Pair the PS5 DualSense via System Settings → Bluetooth first.")
        ser.close()
        sys.exit(1)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"  Controller OK: {joystick.get_name()}")

    # confirmation 
    print("\n" + "=" * 60)
    print("  CONNECTIONS CONFIRMED:")
    print(f"    Serial : {CAMERA_SERVO_PORT}")
    print(f"    Controller : {joystick.get_name()}")
    print("=" * 60)
    print("\nType  YES  and press Enter to begin the test: ", end="", flush=True)
    if input().strip().upper() != "YES":
        print("Aborted.")
        ser.close()
        pygame.quit()
        sys.exit(0)


    print("\n" + "─" * 60)
    print("  CONTROLS:")
    print("    D-pad UP    → tilt up   (toward 180°)")
    print("    D-pad DOWN  → tilt down (toward 0°)")
    print("    Cross (X)   → return to centre (90°)")
    print("    Square      → quit test safely")
    print("─" * 60)

    sweep(ser)

    # live control loop 
    tilt = 90.0
    last_printed = -1
    print("Live control active. Use D-pad to tilt. Press Square to quit.\n")

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

        angle_int = int(round(tilt))
        if angle_int != last_printed:
            send_tilt(ser, angle_int)
            print(f"  Tilt angle: {angle_int:>3}°")
            last_printed = angle_int

        pygame.time.delay(POLL_MS)

    # exit
    print("\nReturning servo to 90° and closing...")
    send_tilt(ser, 90)
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
            ser = serial.Serial(CAMERA_SERVO_PORT, BAUD_RATE, timeout=1)
            time.sleep(1)
            send_tilt(ser, 90)
            ser.close()
            print("Servo returned to 90°.")
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)
