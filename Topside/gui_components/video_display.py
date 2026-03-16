import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class CameraWidget(QWidget):
    """Embeddable camera widget using OpenCV. Create and add to a layout.

    Use `start()` to begin capture (or the widget will start automatically when created).
    """

    def __init__(self, device_index=0, parent=None):
        super().__init__(parent)
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(device_index, cv2.CAP_AVFOUNDATION)
        if not self.cap.isOpened():
            print("Warning: Camera not found at index", device_index)
            self.cap = None
            return

        # Optional camera settings
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        try:
            self.cap.set(cv2.CAP_PROP_EXPOSURE, -7)
            self.cap.set(cv2.CAP_PROP_GAIN, 20)
        except Exception:
            pass

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()


def start_video_feed():
    app = QApplication(sys.argv)
    window = CameraWidget()
    window.setWindowTitle("Camera Feed")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    start_video_feed()