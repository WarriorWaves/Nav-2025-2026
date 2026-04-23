import queue
import pygame
import pygame.joystick

from dataclasses import dataclass, field
from typing import List, Optional

from PyQt5.QtCore import QThread, QTimer, pyqtSignal, QObject

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
class JoystickSnapshot:
    connected:   bool  = False
    axes:        tuple = ()
    buttons:     tuple = ()
    hats:        tuple = ()


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


class ControllerPoller(QObject):
    controller_status = pyqtSignal(bool)

    def __init__(self, snapshot_queue: queue.Queue, parent=None):
        super().__init__(parent)
        self._queue    = snapshot_queue
        self._joystick: Optional[pygame.joystick.Joystick] = None

        pygame.init()
        pygame.joystick.init()
        self._try_connect()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(CONTROLLER_POLL_MS)

    def _try_connect(self):
        if pygame.joystick.get_count() > 0:
            if self._joystick is None:
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()
                print(f"[Controller] Connected: {self._joystick.get_name()}")
                self.controller_status.emit(True)
        else:
            if self._joystick is not None:
                print("[Controller] Disconnected.")
            self._joystick = None
            self.controller_status.emit(False)

    def _poll(self):
        pygame.event.pump()

        if self._joystick is None:
            self._try_connect()

        if self._joystick is not None:
            try:
                snap = JoystickSnapshot(
                    connected = True,
                    axes    = tuple(
                        self._joystick.get_axis(i)
                        for i in range(self._joystick.get_numaxes())
                    ),
                    buttons = tuple(
                        self._joystick.get_button(i)
                        for i in range(self._joystick.get_numbuttons())
                    ),
                    hats    = tuple(
                        self._joystick.get_hat(i)
                        for i in range(self._joystick.get_numhats())
                    ),
                )
            except Exception:
                self._joystick = None
                snap = JoystickSnapshot(connected=False)
        else:
            snap = JoystickSnapshot(connected=False)

        try:
            self._queue.put_nowait(snap)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(snap)

    def stop(self):
        self._timer.stop()
        pygame.quit()


class ROVWorker(QThread):
    state_updated = pyqtSignal(object)

    def __init__(self, snapshot_queue: queue.Queue, parent=None):
        super().__init__(parent)
        self._queue   = snapshot_queue
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
        self._running = True
        while self._running:
            try:
                snap = self._queue.get(timeout=0.1)
            except queue.Empty:
                self.state_updated.emit(self._safe_state(connected=False))
                continue

            state = self._process(snap)
            self.state_updated.emit(state)

        self._send_neutral()
        self.rov_port.close()

    def stop(self):
        self._running = False
        if self.isRunning():
            self.wait()

    def _process(self, snap: JoystickSnapshot) -> ROVState:
        capture_requested = False

        if snap.connected:
            def axis(idx: int) -> float:
                try:    return snap.axes[idx]
                except: return 0.0

            def btn(idx: int) -> bool:
                try:    return bool(snap.buttons[idx])
                except: return False

            def hat(idx: int):
                try:    return snap.hats[idx]
                except: return (0, 0)

            if btn(BTN_SQUARE):
                if not self._estopped:
                    self._estopped = True
                    self._send_neutral()
                    print("[ESTOP] All thrusters -> 1500")
            elif self._estopped:
                if any(btn(b) for b in range(len(snap.buttons)) if b != BTN_SQUARE):
                    self._estopped = False
                    print("[ESTOP] Cleared.")

            if not self._estopped:
                self._do_thrusters(axis)
                self._do_claw(axis)
                self._do_roll(btn)
                self._do_tilt(hat)
                capture_requested = self._do_cross(btn)

        return ROVState(
            thrust_pwm           = list(self._thrust_pwm),
            claw_angle           = int(round(self._claw_position)),
            roll_angle           = int(round(self._roll_position)),
            tilt_angle           = int(round(self._tilt_position)),
            claw_open            = self._claw_open,
            estopped             = self._estopped,
            controller_connected = snap.connected,
            rov_port_connected   = self.rov_port.connected,
            capture_requested    = capture_requested,
        )

    def _safe_state(self, connected: bool) -> ROVState:
        return ROVState(
            thrust_pwm           = list(self._thrust_pwm),
            claw_angle           = int(round(self._claw_position)),
            roll_angle           = int(round(self._roll_position)),
            tilt_angle           = int(round(self._tilt_position)),
            claw_open            = self._claw_open,
            estopped             = self._estopped,
            controller_connected = connected,
            rov_port_connected   = self.rov_port.connected,
            capture_requested    = False,
        )

    def _do_thrusters(self, axis):
        surge = axis(AXIS_LEFT_Y)  * -1
        sway  = axis(AXIS_LEFT_X)
        heave = axis(AXIS_RIGHT_Y) * -1
        yaw   = axis(AXIS_RIGHT_X)
        pwm_dict         = compute_thruster_outputs(surge, sway, heave, yaw)
        self._thrust_pwm = [pwm_dict[n] for n in THRUSTER_ORDER]
        self.rov_port.send("THR " + " ".join(str(v) for v in self._thrust_pwm))

    def _do_claw(self, axis):
        l2 = (axis(AXIS_L2) + 1.0) / 2.0
        r2 = (axis(AXIS_R2) + 1.0) / 2.0
        if l2 > TRIGGER_THRESHOLD:
            self._claw_position = max(CLAW_CLOSED, self._claw_position - CLAW_SPEED * l2)
        elif r2 > TRIGGER_THRESHOLD:
            self._claw_position = min(CLAW_OPEN,   self._claw_position + CLAW_SPEED * r2)
        self._claw_open = self._claw_position > (CLAW_OPEN / 2)
        claw_int = int(round(self._claw_position))
        if claw_int != self._last_claw_sent:
            self.rov_port.send(f"claw:{claw_int}")
            self._last_claw_sent = claw_int

    def _do_roll(self, btn):
        if btn(BTN_L1):
            self._roll_position = max(ROLL_MIN, self._roll_position - ROLL_SPEED)
        elif btn(BTN_R1):
            self._roll_position = min(ROLL_MAX, self._roll_position + ROLL_SPEED)
        roll_int = int(round(self._roll_position))
        if roll_int != self._last_roll_sent:
            self.rov_port.send(f"roll:{roll_int}")
            self._last_roll_sent = roll_int

    def _do_tilt(self, hat):
        h = hat(0)
        self._tilt_position = max(
            TILT_MIN, min(TILT_MAX, self._tilt_position + h[1] * 2.0)
        )
        tilt_int = int(round(self._tilt_position))
        if tilt_int != self._last_tilt_sent:
            self.rov_port.send(f"tilt:{tilt_int}")
            self._last_tilt_sent = tilt_int

    def _do_cross(self, btn) -> bool:
        cross_now            = btn(BTN_CROSS)
        triggered            = cross_now and not self._cross_was_held
        self._cross_was_held = cross_now
        return triggered

    def _send_neutral(self):
        self.rov_port.send(
            "THR " + " ".join(str(THRUSTER_NEUTRAL) for _ in range(6))
        )
        self._thrust_pwm = [THRUSTER_NEUTRAL] * 6


class ROVController(QObject):
    state_updated = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue   = queue.Queue(maxsize=1)
        self._poller  = ControllerPoller(self._queue)
        self._worker  = ROVWorker(self._queue)
        self._worker.state_updated.connect(self.state_updated)

    def start(self):
        self._worker.start()

    def close(self):
        self._poller.stop()
        self._worker.stop()