import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QPainter, QImage, QPixmap


class BarChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 6 thruster powers: V1, V2, D1, D2, D3, D4
        self.values = [0, 0, 0, 0, 0, 0]
        self.labels = ["V1", "V2", "D1", "D2", "D3", "D4"]
        self.setMinimumHeight(150)
        self.setStyleSheet("background-color: #222;")

    def set_values(self, values):
        self.values = values
        self.update()

    def paintEvent(self, even
        painter = QPainter(self)
        bar_width = self.width() // len(self.values)
        max_height = self.height() - 20
        colors = [
            QColor('#3498db'), QColor('#e67e22'),
            QColor("#040404"), QColor('#9b59b6'),
            QColor('#e74c3c'), QColor('#1abc9c')
        ]

        for i, value in enumerate(self.values):
            x = i * bar_width + 10
            h = int((value / 100) * max_height)  # scale to 0–100%
            painter.setBrush(colors[i])
            painter.drawRect(x, self.height() - h - 20, bar_width - 15, h)

            # Draw labels
            painter.setPen(Qt.white)
            painter.drawText(x + bar_width // 4, self.height() - 5, self.labels[i])

        painter.end()


class CameraFeed(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = cv2.VideoCapture(0)  # default camera
        self.setScaledContents(True)

        # Timer to refresh frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.setPixmap(QPixmap.fromImage(qimg))

    def closeEvent(self, event):
        self.cap.release()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ROV GUI")
        self.resize(1000, 600)

        # Set background color
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("black"))
        self.setPalette(palette)

        # Main horizontal layout
        layout = QHBoxLayout(self)

        # Left side: camera feed
        self.camera = CameraFeed()
        layout.addWidget(self.camera, 2)

        # Right side: controls + chart
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Sliders for 6 thrusters
        self.sliders = []
        for i in range(6):
            label = QLabel(f"{['V1','V2','D1','D2','D3','D4'][i]}: 0")
            label.setStyleSheet("color: white; font-size: 14px;")
            right_layout.addWidget(label)

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(0)
            slider.valueChanged.connect(lambda val, l=label, idx=i: self.update_thruster(l, idx, val))
            right_layout.addWidget(slider)
            self.sliders.append(slider)

        # Bar chart
        self.bar_chart = BarChart()
        right_layout.addWidget(self.bar_chart)

        layout.addWidget(right_widget, 1)
        self.setLayout(layout)

    def update_thruster(self, label, idx, val):
        label.setText(f"{['V1','V2','D1','D2','D3','D4'][idx]}: {val}")
        values = [s.value() for s in self.sliders]
        self.bar_chart.set_values(values)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
