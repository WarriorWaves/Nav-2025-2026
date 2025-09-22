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

    def paintEvent(self, even):
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
        self.cap = None
        self.camera_available = False
        self.setScaledContents(True)
        
        # Try to initialize camera with error handling
        self.init_camera()

        # Timer to refresh frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS
    
    def init_camera(self):
        """Initialize camera with fallback options - optimized for Arducam UC-648"""
        print("Initializing camera for Arducam UC-648 Rev.F3...")
        
        # Try different camera indices (prioritize Arducam UC-648 at index 1)
        for camera_index in [1, 0, 2, 3]:
            try:
                print(f"Trying camera index {camera_index}...")
                self.cap = cv2.VideoCapture(camera_index)
                
                if self.cap.isOpened():
                    # Set some properties for better Arducam compatibility
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Test if we can actually read a frame
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        self.camera_available = True
                        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = self.cap.get(cv2.CAP_PROP_FPS)
                        print(f"✅ Arducam UC-648 initialized successfully!")
                        print(f"   Camera index: {camera_index}")
                        print(f"   Resolution: {width}x{height}")
                        print(f"   FPS: {fps}")
                        return
                    else:
                        print(f"   ❌ Camera {camera_index}: Cannot read frames")
                        self.cap.release()
                        self.cap = None
                else:
                    print(f"   ❌ Camera {camera_index}: Cannot open")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
            except Exception as e:
                print(f"   ❌ Camera {camera_index}: Error - {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
        
        # If no camera found, show error message
        if not self.camera_available:
            print("❌ No camera detected. Troubleshooting for Arducam UC-648:")
            print("1. Check USB connection - try a different USB port")
            print("2. Verify in Device Manager: 'Arducam USB Camera' should be listed")
            print("3. Close other applications that might be using the camera")
            print("4. Check Windows camera permissions in Settings > Privacy > Camera")
            print("5. Try unplugging and reconnecting the camera")
            self.setText("Arducam UC-648 Not Found\nCheck USB connection")
            self.setStyleSheet("color: red; font-size: 14px; background-color: #333; padding: 20px;")

    def update_frame(self):
        if not self.camera_available or self.cap is None:
            return
        
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.setPixmap(QPixmap.fromImage(qimg))
        except Exception as e:
            print(f"Error reading camera frame: {e}")
            # Try to reinitialize camera
            self.camera_available = False
            self.init_camera()

    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ROV GUI")
        self.resize(1000, 600)

        # Set background color
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("pink"))
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