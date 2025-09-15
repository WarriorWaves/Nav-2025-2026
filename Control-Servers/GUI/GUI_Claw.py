import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QPainter


class BarChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = [0, 0, 0]
        self.setMinimumHeight(100)
        self.setStyleSheet("background-color: #222;")

    def set_values(self, values):
        self.values = values
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        bar_width = self.width() // 6
        max_height = self.height() - 20
        colors = [QColor('#3498db'), QColor('#e67e22'), QColor('#2ecc71')]
        for i, value in enumerate(self.values):
            x = 30 + i * 2 * bar_width
            h = int((value / 10) * max_height)
            painter.setBrush(colors[i])
            painter.drawRect(x, self.height() - h - 10, bar_width, h)
        painter.end()


class StateGraphic(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = 0
        self.setMinimumHeight(80)
        self.setStyleSheet("background-color: #222;")

    def set_state(self, value):
        self.state = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if 1 <= self.state <= 5:
            painter.setBrush(QColor('#3498db'))
            painter.drawEllipse(self.width()//2-30, self.height()//2-30, 60, 60)
        elif 6 <= self.state <= 10:
            painter.setBrush(QColor('#2ecc71'))
            painter.drawRect(self.width()//2-30, self.height()//2-30, 60, 60)
        painter.end()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Black GUI Split")
        self.resize(800, 600)

        # Set background color to black
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("black"))
        self.setPalette(palette)

        # Main horizontal layout
        layout = QHBoxLayout(self)

        # Left part (3/5 of the width)
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: black;")
        layout.addWidget(left_widget, 2)

        # Right part (2/5 of the width)
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #111;")
        right_layout = QVBoxLayout(right_widget)

        # Label 1 and slider 1
        self.label1 = QLabel("Text 1")
        self.label1.setStyleSheet("color: white; font-size: 16px;")
        self.label1.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.label1)
        self.slider1 = QSlider(Qt.Horizontal)
        self.slider1.setMinimum(0)
        self.slider1.setMaximum(10)
        self.slider1.setValue(0)
        self.slider1.setStyleSheet("background-color: #222;")
        self.slider1.valueChanged.connect(self.update_label1)
        right_layout.addWidget(self.slider1)

        # Label 2 and slider 2
        self.label2 = QLabel("Text 2")
        self.label2.setStyleSheet("color: white; font-size: 16px;")
        self.label2.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.label2)
        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.setMinimum(0)
        self.slider2.setMaximum(10)
        self.slider2.setValue(0)
        self.slider2.setStyleSheet("background-color: #222;")
        self.slider2.valueChanged.connect(self.update_label2)
        right_layout.addWidget(self.slider2)

        # Label 3 and slider 3
        self.label3 = QLabel("Text 3")
        self.label3.setStyleSheet("color: white; font-size: 16px;")
        self.label3.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.label3)
        self.slider3 = QSlider(Qt.Horizontal)
        self.slider3.setMinimum(0)
        self.slider3.setMaximum(10)
        self.slider3.setValue(0)
        self.slider3.setStyleSheet("background-color: #222;")
        self.slider3.valueChanged.connect(self.update_label3)
        right_layout.addWidget(self.slider3)

        # Bar chart
        self.bar_chart = BarChart()
        right_layout.addWidget(self.bar_chart)
        # State graphic
        self.state_graphic = StateGraphic()
        right_layout.addWidget(self.state_graphic)

        right_layout.addStretch()

        layout.addWidget(right_widget, 1)  # stretch factor 1

        self.setLayout(layout)
        self.update_bar_chart()
        self.update_state_graphic()

    def update_label1(self, value):
        if 1 <= value < 10:
            self.label1.setText("low")
        elif 10 <= value < 50:
            self.label1.setText("medium")
        elif 50 <= value <= 200:
            self.label1.setText("high")
        else:
            self.label1.setText(str(value))
        self.update_bar_chart()
        self.update_state_graphic()

    def update_label2(self, value):
        self.label2.setText(f"Value: {value}")
        self.update_bar_chart()

    def update_label3(self, value):
        self.label3.setText(f"Value: {value}")
        self.update_bar_chart()

    def update_bar_chart(self):
        values = [self.slider1.value(), self.slider2.value(), self.slider3.value()]
        self.bar_chart.set_values(values)

    def update_state_graphic(self):
        self.state_graphic.set_state(self.slider1.value())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
