import pygame
import pygame.joystick
from dataclasses import dataclass, field
from typing import List
from PyQt5.QtCore import QThread, pyqtSignal

from utils.serial_comm   import SerialPort
from utils.math_helpers  import compute_thruster_outputs
from config import (
    ROV_PORT, BAUD_RATE,
    THRUSTER_NEUTRAL, THRUSTER_ORDER,
    CLAW_OPEN, CLAW_CLOSED, CLAW_SPEED,
    ROLL_MIN, ROLL_MAX, ROLL_SPEED,
    TILT_MIN, TILT_MAX,
    AXIS_LEFT_X, AXIS_LEFT_Y, AXIS_RIGHT_X, AXIS_RIGHT_Y,
    AXIS_L2, AXIS_R2,
    BTN_L1, BTN_R1, BTN_SQUARE, BTN_CROSS,
    TRIGGER_THRESHOLD,
    CONTROLLER_POLL_MS,
)


@dataclass
class ROVState:
    thrust_pwm:           List[int] = field(default_factory=lambda: [THRUSTER_NEUTRAL] * 6)
    claw_angle:           int  = CLAW_OPEN
    roll_angle:           int  = 90
    tilt_angle:           int  = 90
    claw_open:            bool = True
    estopped:             bool = False
    controller_connected: bool = False
    rov_port_connected:   bool = False
    capture_requested:    bool = False


class ROVWorker(QThread):
    state_updated = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False

        self.rov_port = SerialPort(ROV_PORT, BAUD_RATE, name="ROV Arduino")

        self._claw_position  = float(CLAW_OPEN)
        self._roll_position  = 90.0
        self._tilt_position  = 90.0
        self._estopped       = False
        self._claw_open      = True
        self._last_claw_sent = -1
        self._last_roll_sent = -1
        self._last_tilt_sent = -1
        self._cross_was_held = False
        self._thrust_pwm     = [THRUSTER_NEUTRAL] * 6

    def run(self):
        pygame.joystick.init()

        joystick      = self._connect_joystick()
        self._running = True

        while self._running:
            pygame.event.pump()

            if joystick is None:
                joystick = self._connect_joystick()
            else:
                try:
                    joystick.get_name()
                except Exception:
                    print("[Worker] Controller disconnected.")
                    joystick = None

            state = self._poll(joystick)
            self.state_updated.emit(state)

            self.msleep(CONTROLLER_POLL_MS)

        self._send_neutral()
        self.rov_port.close()
        pygame.joystick.quit()

    def stop(self):
        self._running = False
        if self.isRunning():
            self.wait()

    def _poll(self, joystick) -> ROVState:
        capture_requested = False

        if joystick is not None:
            if self._btn(joystick, BTN_SQUARE):
                if not self._estopped:
                    self._estopped = True
                    self._send_neutral()
                    print("[ESTOP] All thrusters -> 1500")
            elif self._estopped:
                if any(
                    joystick.get_button(b)
                    for b in range(joystick.get_numbuttons())
                    if b != BTN_SQUARE
                ):
                    self._estopped = False
                    print("[ESTOP] Cleared.")

            if not self._estopped:
                self._handle_thrusters(joystick)
                self._handle_claw(joystick)
                self._handle_roll(joystick)
                self._handle_tilt(joystick)
                capture_requested = self._handle_cross(joystick)

        return ROVState(
            thrust_pwm           = list(self._thrust_pwm),
            claw_angle           = int(round(self._claw_position)),
            roll_angle           = int(round(self._roll_position)),
            tilt_angle           = int(round(self._tilt_position)),
            claw_open            = self._claw_open,
            estopped             = self._estopped,
            controller_connected = joystick is not None,
            rov_port_connected   = self.rov_port.connected,
            capture_requested    = capture_requested,
        )

    def _handle_thrusters(self, joystick):
        surge = self._axis(joystick, AXIS_LEFT_Y)  * -1
        sway  = self._axis(joystick, AXIS_LEFT_X)
        heave = self._axis(joystick, AXIS_RIGHT_Y) * -1
        yaw   = self._axis(joystick, AXIS_RIGHT_X)
        pwm_dict         = compute_thruster_outputs(surge, sway, heave, yaw)
        self._thrust_pwm = [pwm_dict[n] for n in THRUSTER_ORDER]
        self.rov_port.send("THR " + " ".join(str(v) for v in self._thrust_pwm))

    def _handle_claw(self, joystick):
        l2 = (self._axis(joystick, AXIS_L2) + 1.0) / 2.0
        r2 = (self._axis(joystick, AXIS_R2) + 1.0) / 2.0
        if l2 > TRIGGER_THRESHOLD:
            self._claw_position = max(CLAW_CLOSED, self._claw_position - CLAW_SPEED * l2)
        elif r2 > TRIGGER_THRESHOLD:
            self._claw_position = min(CLAW_OPEN,   self._claw_position + CLAW_SPEED * r2)
        self._claw_open = self._claw_position > (CLAW_OPEN / 2)
        claw_int = int(round(self._claw_position))
        if claw_int != self._last_claw_sent:
            self.rov_port.send(f"claw:{claw_int}")
            self._last_claw_sent = claw_int

    def _handle_roll(self, joystick):
        if self._btn(joystick, BTN_L1):
            self._roll_position = max(ROLL_MIN, self._roll_position - ROLL_SPEED)
        elif self._btn(joystick, BTN_R1):
            self._roll_position = min(ROLL_MAX, self._roll_position + ROLL_SPEED)
        roll_int = int(round(self._roll_position))
        if roll_int != self._last_roll_sent:
            self.rov_port.send(f"roll:{roll_int}")
            self._last_roll_sent = roll_int

    def _handle_tilt(self, joystick):
        if joystick.get_numhats() > 0:
            hat = joystick.get_hat(0)
            self._tilt_position = max(
                TILT_MIN, min(TILT_MAX, self._tilt_position + hat[1] * 2.0)
            )
        tilt_int = int(round(self._tilt_position))
        if tilt_int != self._last_tilt_sent:
            self.rov_port.send(f"tilt:{tilt_int}")
            self._last_tilt_sent = tilt_int

    def _handle_cross(self, joystick) -> bool:
        cross_now            = self._btn(joystick, BTN_CROSS)
        triggered            = cross_now and not self._cross_was_held
        self._cross_was_held = cross_now
        return triggered

    def _connect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            print(f"[Worker] Controller connected: {js.get_name()}")
            return js
        return None

    def _send_neutral(self):
        self.rov_port.send(
            "THR " + " ".join(str(THRUSTER_NEUTRAL) for _ in range(6))
        )
        self._thrust_pwm = [THRUSTER_NEUTRAL] * 6

    @staticmethod
    def _axis(j, idx: int) -> float:
        try:    return j.get_axis(idx)
        except: return 0.0

    @staticmethod
    def _btn(j, idx: int) -> bool:
        try:    return bool(j.get_button(idx))
        except: return False


class ROVController:
    def __init__(self):
        self._worker = ROVWorker()

    @property
    def state_updated(self):
        return self._worker.state_updated

    def start(self):
        self._worker.start()

    def close(self):
        self._worker.stop()