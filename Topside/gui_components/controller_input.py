import time
import pygame
from PyQt5.QtCore import QThread, pyqtSignal


class PS5ControllerThread(QThread):

    valuesChanged = pyqtSignal(dict)
    statusChanged = pyqtSignal(str, str)

    def __init__(self, poll_interval=0.03, axis_map=None):
        super().__init__()
        self.poll_interval = poll_interval
        self.running = True
        pygame.init()
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Default mapping: axis 0..5 -> sliders V1,V2,D1..D4
        self.axis_map = axis_map or {
            0: 'V1',
            1: 'V2',
            2: 'D1',
            3: 'D2',
            4: 'D3',
            5: 'D4',
        }

    def run(self):
        if not self.joystick:
            # no controller found — exit thread cleanly
            return
        while self.running:
            pygame.event.pump()
            values = {}
            for axis_idx, name in self.axis_map.items():
                if axis_idx < self.joystick.get_numaxes():
                    raw = self.joystick.get_axis(axis_idx)
                    # convert -1..1 -> 0..100
                    val = int((raw + 1) / 2 * 100)
                    values[name] = max(0, min(100, val))

            # Example button mapping: use button 0 to toggle claw WARN/OK
            try:
                btn0 = False
                if self.joystick.get_numbuttons() > 0:
                    btn0 = bool(self.joystick.get_button(0))
                self.statusChanged.emit('Claw', 'WARN' if btn0 else 'OK')
            except Exception:
                pass

            if values:
                self.valuesChanged.emit(values)

            time.sleep(self.poll_interval)

    def stop(self):
        self.running = False
        self.wait()


def read_controller():
    return PS5ControllerThread()
