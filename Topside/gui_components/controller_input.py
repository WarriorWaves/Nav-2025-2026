import pygame
from PyQt5.QtCore import QThread, pyqtSignal


class PS5ControllerThread(QThread):
    valuesChanged = pyqtSignal(dict)
    statusChanged = pyqtSignal(str, str)

    def __init__(self, poll_interval_ms: int = 30, axis_map: dict = None):
        super().__init__()
        self.poll_interval_ms = poll_interval_ms
        self.running = True

        self.axis_map = axis_map or {
            0: 'LeftX',
            1: 'LeftY',
            2: 'RightX',
            3: 'RightY',
            4: 'L2',
            5: 'R2',
        }

    def run(self):
        pygame.init()
        pygame.joystick.init()

        joystick = None
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
        else:
            self.statusChanged.emit('Controller', 'NOT FOUND')
            pygame.quit()
            return

        while self.running:
            pygame.event.pump()

            values = {}
            for axis_idx, name in self.axis_map.items():
                if axis_idx < joystick.get_numaxes():
                    values[name] = joystick.get_axis(axis_idx)

            try:
                if joystick.get_numbuttons() > 0:
                    cross = bool(joystick.get_button(0))
                    self.statusChanged.emit('Claw', 'WARN' if cross else 'OK')
            except Exception:
                pass

            if values:
                self.valuesChanged.emit(values)

            self.msleep(self.poll_interval_ms)

        pygame.quit()

    def stop(self):
        self.running = False
        if self.isRunning():
            self.wait()


def read_controller(poll_interval_ms: int = 30) -> PS5ControllerThread:
    thread = PS5ControllerThread(poll_interval_ms=poll_interval_ms)
    thread.start()
    return thread