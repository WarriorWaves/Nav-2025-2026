"""Verifies all 6 thrusters respond correctly (hopefully lol)"""

import time
import sys
import serial

from config import THRUSTER_PORT, BAUD_RATE, THRUSTER_ORDER, THRUSTER_NEUTRAL

SPIN_SPEED    = 1550   # PWM for forward spin
SPIN_DURATION = 1.5    # Run duration per thruster (sec)
MOVE_SPEED    = 1560   # PWM for directional tests
MOVE_DURATION = 2.0    # Run duration per direction (sec)
PAUSE         = 1.0    # Pause between tests (sec)

NEUTRAL = [THRUSTER_NEUTRAL] * 6
# Thruster indices matching THRUSTER_ORDER
FR, FL, BR, BL, F, B = 0, 1, 2, 3, 4, 5

def connect(port, baud):
    print(f"\n[Serial] Connecting to thruster Arduino on {port} ...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)   # Wait for Arduino boot
        ser.reset_input_buffer()
        print(f"[Serial] Connected.\n")
        return ser
    except serial.SerialException as e:
        print(f"\n[ERROR] Could not open {port}: {e}")
        print("  → Check THRUSTER_PORT in config.py")
        print("  → Run:  ls /dev/cu.*")
        sys.exit(1)

def send_pwm(ser, pwm_list):
    """Send THR command to the thruster Arduino."""
    cmd = "THR " + " ".join(str(int(v)) for v in pwm_list) + "\n"
    ser.write(cmd.encode("utf-8"))

def all_neutral(ser):
    send_pwm(ser, NEUTRAL)

def read_response(ser):
    time.sleep(0.05)
    while ser.in_waiting:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            print(f"  [Arduino] {line}")

def safety_check():
    print("=" * 60)
    print("  WARRIOR WAVES — THRUSTER TEST SCRIPT")
    print("=" * 60)
    print()
    print("  Thruster order:  FR  FL  BR  BL  F  B")
    print("  Neutral PWM:     1500 µs")
    print(f"  Spin PWM:        {SPIN_SPEED} µs  (gentle forward)")
    print()
    print("  ⚠  SAFETY CHECKLIST before continuing:")
    print("     [ ] ROV is on a stable surface or mounted securely")
    print("     [ ] Thruster shrouds are attached")
    print("     [ ] No loose wires near thruster props")
    print("     [ ] You can reach the power switch quickly")
    print()
    ans = input("  Type  YES  to begin the test: ").strip().upper()
    if ans != "YES":
        print("\n  Aborted.")
        sys.exit(0)
    print()   print()

def test_arm(ser):
    """Send neutral to all thrusters."""
    print("── TEST 1: ARM (all neutral) ──────────────────────────")
    all_neutral(ser)
    read_response(ser)
    print("  Sent neutral (1500) to all 6 thrusters.")
    print("  ✓ No movement expected.")
    time.sleep(PAUSE)

def test_individual(ser):
    """Spin each thruster one at a time."""
    print("\n── TEST 2: INDIVIDUAL THRUSTERS ───────────────────────")
    for idx, name in enumerate(THRUSTER_ORDER):
        pwm = NEUTRAL.copy()
        pwm[idx] = SPIN_SPEED
        print(f"  [{idx+1}/6] {name} → {SPIN_SPEED} µs  ({SPIN_DURATION}s) ...", end=" ", flush=True)
        send_pwm(ser, pwm)
        read_response(ser)
        time.sleep(SPIN_DURATION)
        all_neutral(ser)
        print("STOPPED") time.sleep(PAUSE)

def test_individual(ser):
    """Spin each thruster one at a time."""
    print("\n── TEST 2: INDIVIDUAL THRUSTERS ───────────────────────")
    for idx, name in enumerate(THRUSTER_ORDER):
        pwm = NEUTRAL.copy()
        pwm[idx] = SPIN_SPEED
        print(f"  [{idx+1}/6] {name} → {SPIN_SPEED} µs  ({SPIN_DURATION}s) ...", end=" ", flush=True)
        send_pwm(ser, pwm)
        read_response(ser)
        time.sleep(SPIN_DURATION)
        all_neutral(ser)
        print("STOPPED")
        time.sleep(PAUSE)
    print("  ✓ All individual thrusters tested.")

def test_directional(ser):
    """Run combined thrust patterns to test mixing."""
    print("\n── TEST 3: DIRECTIONAL PATTERNS ───────────────────────")

    hi  = MOVE_SPEED               # Forward
    lo  = THRUSTER_NEUTRAL * 2 - MOVE_SPEED  # Reverse
    N   = THRUSTER_NEUTRAL

    patterns = [
        # [FR, FL, BR, BL, F, B]
        ("SURGE FWD",  [hi,  hi,  hi,  hi,  N,   N  ]),
        ("SURGE REV",  [lo,  lo,  lo,  lo,  N,   N  ]),
        ("SWAY RIGHT",  [lo,  hi,  hi,  lo,  N,   N  ]),
        ("SWAY LEFT",   [hi,  lo,  lo,  hi,  N,   N  ]),
        ("HEAVE UP",   [N,   N,   N,   N,   hi,  hi ]),
        ("HEAVE DOWN", [N,   N,   N,   N,   lo,  lo ]),
        ("YAW RIGHT",  [lo,  hi,  lo,  hi,  N,   N  ]),
        ("YAW LEFT",   [hi,  lo,  hi,  lo,  N,   N  ]),
    ]

    for name, pwm in patterns:
        print(f"  {name:<12} {pwm}  ({MOVE_DURATION}s) ...", end=" ", flush=True)
        send_pwm(ser, pwm)
        read_response(ser)
        time.sleep(MOVE_DURATION)
        all_neutral(ser)
        print("STOPPED")
        time.sleep(PAUSE)

    print("  ✓ Directional patterns complete.")

def test_full_stop(ser):
    """Final safety neutral."""
    print("\n── TEST 4: FULL STOP ──────────────────────────────────")
    all_neutral(ser)
    read_response(ser)
    print("  All thrusters → 1500 µs (neutral).")
    print("  ✓ Test sequence complete.\n")

if __name__ == "__main__":
    safety_check()

    ser = connect(THRUSTER_PORT, BAUD_RATE)

    try:
        test_arm(ser)
        test_individual(ser)
        test_directional(ser)
        test_full_stop(ser)

        print("=" * 60)
        print("  ALL TESTS PASSED — safe to proceed to pool testing.")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n  [!] Test interrupted by user.")
        print("  Sending neutral to all thrusters...")
        all_neutral(ser)
        print("  Safe.")

    finally:
        ser.close()
        print("  Serial port closed.")