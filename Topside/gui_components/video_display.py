import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


def start_video_feed():
    class CameraViewer(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("Camera Feed")
            self.setGeometry(100, 100, 800, 600)

            # Label to display video
            self.video_label = QLabel(self)
            self.video_label.setAlignment(Qt.AlignCenter)

            layout = QVBoxLayout()
            layout.addWidget(self.video_label)
            self.setLayout(layout)

            # OpenCV video capture
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Change to 1 if needed
            if not self.cap.isOpened():
                print("Error: Camera not found!")
                sys.exit()

            # Optional camera settings
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            self.cap.set(cv2.CAP_PROP_EXPOSURE, -7)
            self.cap.set(cv2.CAP_PROP_GAIN, 20)

            # Timer to update frames
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(30)  # ~33 FPS

        def update_frame(self):
            ret, frame = self.cap.read()
            if not ret:
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            self.video_label.setPixmap(QPixmap.fromImage(qimg))

        def closeEvent(self, event):
            if self.cap.isOpened():
                self.cap.release()
            event.accept()

    app = QApplication(sys.argv)
    window = CameraViewer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    start_video_feed()