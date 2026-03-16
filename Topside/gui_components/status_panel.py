import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QPainter

# Import controller and camera widget from the same package; support running as script
try:
    from controller_input import PS5ControllerThread
except Exception:
    from .controller_input import PS5ControllerThread

try:
    from video_display import CameraWidget
except Exception:
    from .video_display import CameraWidget

class StatusPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#1e1e1e"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.labels = {}
        for name in ["ROV Power", "Thrusters", "Claw", "Camera"]:
            lbl = QLabel(f"{name}: OK")
            lbl.setStyleSheet("color: #00ff00; font-weight: bold;")
            layout.addWidget(lbl)
            self.labels[name] = lbl
        layout.addStretch(1)

    def update_status(self, name, value):
        if name in self.labels:
            self.labels[name].setText(f"{name}: {value}")
            color = "#00ff00" if value == "OK" else "#ffff00" if value == "WARN" else "#ff0000"
            self.labels[name].setStyleSheet(f"color: {color}; font-weight: bold;")

class GraphWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.values = [0] * 6
        self.setFixedHeight(150)
        self.setStyleSheet("background-color: #222222; border: 2px solid black;")

    def set_values(self, values):
        self.values = values
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        bar_width = w / len(self.values)
        for i, val in enumerate(self.values):
            bar_height = (val / 100) * (h - 10)
            painter.fillRect(
                int(i * bar_width + 5),
                int(h - bar_height - 5),
                int(bar_width - 10),
                int(bar_height),
                QColor("#00ff00")
            )

class ROVGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROV GUI")
        self.setGeometry(100, 100, 1000, 700)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#ffb6c1"))
        self.setPalette(palette)
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        # Embedded camera widget
        self.camera_widget = CameraWidget()
        try:
            self.camera_widget.setFixedSize(640, 480)
        except Exception:
            pass
        main_layout.addWidget(self.camera_widget, stretch=3)
        side_layout = QVBoxLayout()
        main_layout.addLayout(side_layout, stretch=1)
        self.status_panel = StatusPanel()
        side_layout.addWidget(self.status_panel)
        self.sliders = {}
        for name in ["V1", "V2", "D1", "D2", "D3", "D4"]:
            lbl = QLabel(f"{name}: 0")
            sld = QSlider(Qt.Horizontal)
            sld.setRange(0, 100)
            sld.valueChanged.connect(lambda val, n=name, l=lbl: l.setText(f"{n}: {val}"))
            sld.valueChanged.connect(self.update_graph)
            side_layout.addWidget(lbl)
            side_layout.addWidget(sld)
            self.sliders[name] = (lbl, sld)
        self.graph = GraphWidget()
        side_layout.addWidget(self.graph)
        self.cap = None
        # Start PS5 controller thread (if a controller is connected)
        self.controller = PS5ControllerThread()
        self.controller.valuesChanged.connect(self.on_controller_values)
        self.controller.statusChanged.connect(self.status_panel.update_status)
        self.controller.start()

    def update_graph(self):
        values = [self.sliders[n][1].value() for n in self.sliders]
        self.graph.set_values(values)

    def on_controller_values(self, values: dict):
        # Update sliders from controller axis values
        for name, val in values.items():
            if name in self.sliders:
                _, sld = self.sliders[name]
                # avoid recursive signals by blocking signals temporarily
                sld.blockSignals(True)
                sld.setValue(int(val))
                sld.blockSignals(False)

    def closeEvent(self, event):
        try:
            if self.controller:
                self.controller.stop()
        except Exception:
            pass
        try:
            if hasattr(self, 'camera_widget') and self.camera_widget is not None:
                self.camera_widget.close()
        except Exception:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ROVGui()
    win.show()
    sys.exit(app.exec_())