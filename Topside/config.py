import numpy as np

ROV_PORT  = "/dev/cu.usbserial-14240" #UPDATE THIS!! To the actual port
BAUD_RATE = 9600

CAMERA_INDEX_FRONT = 0
CAMERA_INDEX_REAR  = 1
CAMERA_WIDTH       = 640
CAMERA_HEIGHT      = 480
CAMERA_FPS         = 15

THRUSTER_ORDER   = ["FR", "FL", "BR", "BL", "F", "B"]
THRUSTER_NEUTRAL = 1500
THRUSTER_MIN     = 1350
THRUSTER_MAX     = 1650

MIXING_MATRIX = np.array([
    [ 1, -1,  0, -1],
    [ 1,  1,  0,  1],
    [ 1,  1,  0, -1],
    [ 1, -1,  0,  1],
    [ 0,  0,  1,  0],
    [ 0,  0,  1,  0],
], dtype=float)

CLAW_OPEN   = 180
CLAW_CLOSED = 0
CLAW_SPEED  = 1.5

ROLL_MIN   = 0
ROLL_MAX   = 180
ROLL_SPEED = 1.0

TILT_MIN = 0
TILT_MAX = 180

AXIS_LEFT_X  = 0
AXIS_LEFT_Y  = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
AXIS_L2      = 4
AXIS_R2      = 5

BTN_CROSS   = 0
BTN_SQUARE  = 2
BTN_L1      = 9
BTN_R1      = 10

TRIGGER_THRESHOLD = 0.15
AXIS_DEADZONE     = 0.08

CONTROLLER_POLL_MS = 30
VIDEO_UPDATE_MS    = 33
GUI_UPDATE_MS      = 50