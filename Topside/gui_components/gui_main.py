import sys
import os
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QGroupBox, QProgressBar,
    QSizePolicy, QFrame,
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pygame_controller import ROVController
from config import VIDEO_UPDATE_MS, THRUSTER_ORDER, BTN_CROSS

_OK    = "#4CAF50"
_ERROR = "#f44336"

class VideoFeedWidget(QLabel):

    def __init__(self, title: str = "Video Feed", camera_index: int = 0, parent=None):
        super().__init__(parent)
        self._title = title
        self.setMinimumSize(480, 270)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            border: 2px solid #3d3d3d;
            border-radius: 8px;
            background-color: #1a1a1a;
            color: #888;
        """)
        self.setText(f"{title}\nNo Signal")

        self.capture = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
        if self.capture.isOpened():
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._update_feed)
            self._timer.start(VIDEO_UPDATE_MS)
        else:
            print(f"[Camera] Could not open camera index {camera_index}")

    def _update_feed(self):
        if not self.capture or not self.capture.isOpened():
            return
        ret, frame = self.capture.read()
        if not ret:
            self.setText(f"{self._title}\nNo Signal")
            return
        lw, lh = self.width(), self.height()
        if lw <= 0 or lh <= 0:
            return
        fh, fw = frame.shape[:2]
        ar = fw / fh
        if lw / lh > ar:
            nh, nw = lh, int(lh * ar)
        else:
            nw, nh = lw, int(lw / ar)
        frame_r = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
        canvas  = np.zeros((lh, lw, 3), dtype=np.uint8)
        xo = (lw - nw) // 2
        yo = (lh - nh) // 2
        canvas[yo:yo + nh, xo:xo + nw] = frame_r
        rgb   = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        h, w, c = rgb.shape
        qimg  = QImage(rgb.data, w, h, c * w, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qimg))

    def capture_frame(self):
        if not self.capture or not self.capture.isOpened():
            return False
        ret, frame = self.capture.read()
        if ret:
            path = os.path.expanduser("~/Desktop/rov_capture.png")
            cv2.imwrite(path, frame)
            print(f"[Camera] Photo saved: {path}")
            return True
        return False

    def release(self):
        if self.capture and self.capture.isOpened():
            self.capture.release()

class ThrusterPowerWidget(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel(name)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 9, QFont.Bold))
        title.setStyleSheet("color: #ccc; border: none;")

        self._bar = QProgressBar()
        self._bar.setOrientation(Qt.Vertical)
        self._bar.setRange(-100, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setMinimumHeight(120)
        self._bar.setFixedWidth(28)

        self._label = QLabel("0%")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setFont(QFont("Arial", 8))
        self._label.setStyleSheet("color: #aaa; border: none;")

        layout.addWidget(title)
        layout.addWidget(self._bar, alignment=Qt.AlignHCenter)
        layout.addWidget(self._label)

    def update_power(self, power: float):
        p = int(max(-100, min(100, power)))
        self._bar.setValue(p)
        self._label.setText(f"{p:+d}%")
        colour = "#4CAF50" if p > 0 else ("#f44336" if p < 0 else "#555")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #222;
            }}
            QProgressBar::chunk {{
                background-color: {colour};
                border-radius: 2px;
            }}
        """)

class ThrusterPowerPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Thruster Power", parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        self._widgets = {}
        for name in THRUSTER_ORDER:
            w = ThrusterPowerWidget(name)
            self._widgets[name] = w
            layout.addWidget(w)
        self.setStyleSheet("""
            QGroupBox {
                background-color: #1e1e1e;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 1em;
                padding: 8px;
                color: white;
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)

    def update_thrusters(self, pwm_list):
        for i, name in enumerate(THRUSTER_ORDER):
            power = (pwm_list[i] - 1500) / 1.5
            self._widgets[name].update_power(power)

class StatusPanel(QGroupBox):
    _ROWS = ["Controller", "ROV Port", "E-Stop"]

    def __init__(self, parent=None):
        super().__init__("System Status", parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        self._labels = {}
        for name in self._ROWS:
            row     = QHBoxLayout()
            lbl_name = QLabel(name)
            lbl_name.setFont(QFont("Arial", 10))
            lbl_name.setStyleSheet("color: #aaa; border: none;")
            lbl_name.setFixedWidth(110)
            lbl_val = QLabel("--")
            lbl_val.setFont(QFont("Arial", 10, QFont.Bold))
            lbl_val.setStyleSheet("color: #555; border: none;")
            row.addWidget(lbl_name)
            row.addWidget(lbl_val)
            row.addStretch()
            layout.addLayout(row)
            self._labels[name] = lbl_val
        self.setStyleSheet("""
            QGroupBox {
                background-color: #1e1e1e;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 1em;
                padding: 8px;
                color: white;
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)

    def set(self, name: str, text: str, colour: str):
        if name in self._labels:
            self._labels[name].setText(text)
            self._labels[name].setStyleSheet(
                f"color: {colour}; border: none; font-weight: bold;"
            )

class EStopBanner(QLabel):
    def __init__(self, parent=None):
        super().__init__("⚠ EMERGENCY STOP ⚠", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 18, QFont.Bold))
        self.setStyleSheet("""
            background-color: #c62828;
            color: white;
            padding: 10px;
            border-radius: 6px;
            letter-spacing: 3px;
        """)
        self.setFixedHeight(55)
        self.hide()

class ClawStatusWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame { background-color: #1e1e1e; border: 2px solid #3d3d3d; border-radius: 8px; }
        """)
        layout = QHBoxLayout(self)
        lbl = QLabel("CLAW:")
        lbl.setFont(QFont("Arial", 11, QFont.Bold))
        lbl.setStyleSheet("color: #aaa; border: none;")
        self._ind = QLabel("OPEN")
        self._ind.setFont(QFont("Arial", 11, QFont.Bold))
        self._ind.setStyleSheet("color: #4CAF50; border: none;")
        layout.addWidget(lbl)
        layout.addWidget(self._ind)
        layout.addStretch()

    def update_status(self, is_open: bool):
        self._ind.setText("OPEN" if is_open else "CLOSED")
        self._ind.setStyleSheet(
            f"color: {'#4CAF50' if is_open else '#f44336'}; border: none; font-weight: bold;"
        )

class CameraTiltReadout(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame { background-color: #1e1e1e; border: 2px solid #3d3d3d; border-radius: 8px; }
        """)
        layout = QHBoxLayout(self)
        lbl = QLabel("CAM TILT:")
        lbl.setFont(QFont("Arial", 11, QFont.Bold))
        lbl.setStyleSheet("color: #aaa; border: none;")
        self._val = QLabel("90°")
        self._val.setFont(QFont("Arial", 11, QFont.Bold))
        self._val.setStyleSheet("color: #64B5F6; border: none;")
        layout.addWidget(lbl)
        layout.addWidget(self._val)
        layout.addStretch()

    def update_tilt(self, angle: int):
        self._val.setText(f"{angle}°")

class ROVControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warrior Waves ROV — Control Panel")
        self.setStyleSheet("background-color: #121212; color: white;")

        self._controller = ROVController()
        self._controller.state_updated.connect(self._on_state_updated)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._estop_banner = EStopBanner()
        root.addWidget(self._estop_banner)

        main_row = QHBoxLayout()
        main_row.setSpacing(10)
        root.addLayout(main_row, stretch=1)

        left = QVBoxLayout()
        left.setSpacing(8)
        self._thruster_panel = ThrusterPowerPanel()
        self._status_panel   = StatusPanel()
        left.addWidget(self._thruster_panel)
        left.addWidget(self._status_panel)
        left.addStretch()
        main_row.addLayout(left)

        centre = QVBoxLayout()
        centre.setSpacing(8)
        self._feed1 = VideoFeedWidget("Camera 1 (Front)", camera_index=0)
        self._feed2 = VideoFeedWidget("Camera 2 (Rear)",  camera_index=1)
        centre.addWidget(self._feed1)
        centre.addWidget(self._feed2)
        main_row.addLayout(centre, stretch=2)

        right = QVBoxLayout()
        right.setSpacing(8)
        self._claw_status  = ClawStatusWidget()
        self._tilt_readout = CameraTiltReadout()
        right.addWidget(self._claw_status)
        right.addWidget(self._tilt_readout)
        right.addStretch()
        main_row.addLayout(right)

        self._controller.start()

    def _on_state_updated(self, state):
        self._thruster_panel.update_thrusters(state.thrust_pwm)
        self._claw_status.update_status(state.claw_open)
        self._tilt_readout.update_tilt(state.tilt_angle)
        self._estop_banner.setVisible(state.estopped)

        self._status_panel.set(
            "Controller",
            "CONNECTED" if state.controller_connected else "DISCONNECTED",
            _OK if state.controller_connected else _ERROR,
        )
        self._status_panel.set(
            "ROV Port",
            "OK" if state.rov_port_connected else "NO PORT",
            _OK if state.rov_port_connected else _ERROR,
        )
        self._status_panel.set(
            "E-Stop",
            "ACTIVE" if state.estopped else "READY",
            _ERROR if state.estopped else _OK,
        )

        if state.capture_requested:
            self._feed1.capture_frame()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C:
            self._feed1.capture_frame()

    def closeEvent(self, event):
        self._controller.close()
        self._feed1.release()
        self._feed2.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Warrior Waves ROV")
    window = ROVControlPanel()
    window.showMaximized()
    sys.exit(app.exec_())