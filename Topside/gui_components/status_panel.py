import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor

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
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        self.video_label.setFrameShape(QFrame.Box)
        self.video_label.setLineWidth(5)
        self.video_label.setStyleSheet("border-color: #333333; background-color: black;")
        main_layout.addWidget(self.video_label, stretch=3)
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
            side_layout.addWidget(lbl)
            side_layout.addWidget(sld)
            self.sliders[name] = (lbl, sld)
        self.graph = QLabel()
        self.graph.setFixedHeight(150)
        self.graph.setStyleSheet("background-color: #222222; border: 2px solid black;")
        side_layout.addWidget(self.graph)
        self.cap = None
        for i in range(5):
            temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if temp_cap.isOpened():
                self.cap = temp_cap
                print(f"Camera found at index {i}")
                break
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            self.cap.set(cv2.CAP_PROP_EXPOSURE, -7)
            self.cap.set(cv2.CAP_PROP_GAIN, 20)
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(30)
        else:
            print("Warning: No camera found! Video feed disabled.")

    def update_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ROVGui()
    win.show()
    sys.exit(app.exec_())
