import sys
import os
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import VIDEO_UPDATE_MS


class CameraWidget(QWidget):
    """
    cam widget using OpenCV.
    Feed starts automatically on construction

    This widget is for standalone or diagnostic use.
    """

    def __init__(self, device_index: int = 0, parent=None):
        super().__init__(parent)

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(device_index, cv2.CAP_AVFOUNDATION)
        if not self.cap.isOpened():
            print(f"[CameraWidget] Warning: no camera at index {device_index}")
            self.cap = None
            return

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        try:
            self.cap.set(cv2.CAP_PROP_EXPOSURE, -7)
            self.cap.set(cv2.CAP_PROP_GAIN, 20)
        except Exception:
            pass


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(VIDEO_UPDATE_MS)

    def update_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()



def start_video_feed(device_index: int = 0):
    app = QApplication(sys.argv)
    window = CameraWidget(device_index=device_index)
    window.setWindowTitle(f"Camera Feed — device {device_index}")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    start_video_feed()