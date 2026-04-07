from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QPalette, QColor


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
        for name in ["Controller", "ROV Port", "Thrusters", "Claw", "CameraServo", "E-Stop"]:
            lbl = QLabel(f"{name}: --")
            lbl.setStyleSheet("color: #555555; font-weight: bold;")
            layout.addWidget(lbl)
            self.labels[name] = lbl

        layout.addStretch(1)

    def update_status(self, name: str, value: str):
        if name not in self.labels:
            return
        self.labels[name].setText(f"{name}: {value}")
        if value in ("OK", "CONNECTED", "READY"):
            colour = "#4CAF50"
        elif value == "WARN":
            colour = "#ffff00"
        else:
            colour = "#f44336"
        self.labels[name].setStyleSheet(f"color: {colour}; font-weight: bold;")