import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor


class ROVGui(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ROV GUI")
        self.setGeometry(100, 100, 1000, 700)

        # Background color
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#ffb6c1"))  # pink
        self.setPalette(palette)

        # Layouts
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Camera frame
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        self.video_label.setFrameShape(QFrame.Box)
        self.video_label.setLineWidth(5)
        self.video_label.setStyleSheet("border-color: #333333; background-color: black;")
        main_layout.addWidget(self.video_label, stretch=3)

        # Right panel
        side_layout = QVBoxLayout()
        main_layout.addLayout(side_layout, stretch=1)

        # Sliders
        self.sliders = {}
        for name in ["V1", "V2", "D1", "D2", "D3", "D4"]:
            lbl = QLabel(f"{name}: 0")
            sld = QSlider(Qt.Horizontal)
            sld.setRange(0, 100)
            sld.valueChanged.connect(lambda val, n=name, l=lbl: l.setText(f"{n}: {val}"))
            side_layout.addWidget(lbl)
            side_layout.addWidget(sld)
            self.sliders[name] = (lbl, sld)

        # Graph placeholder
        self.graph = QLabel()
        self.graph.setFixedHeight(150)
        self.graph.setStyleSheet("background-color: #222222; border: 2px solid black;")
        side_layout.addWidget(self.graph)

        # OpenCV video capture
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("Error: Camera not found!")
            sys.exit()

        # Force MJPEG color stream
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        # Exposure / gain
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -7)
        self.cap.set(cv2.CAP_PROP_GAIN, 20)

        # Timer to update frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Convert to QImage
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(qimg)

        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def closeEvent(self, event):
        if self.cap.isOpened():
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ROVGui()
    win.show()
    sys.exit(app.exec_())