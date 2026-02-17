from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSlider
from PyQt5.QtCore import Qt

class ClawPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.sliders = {}
        for name in ["Claw Grip", "Claw Rotation"]:
            lbl = QLabel(f"{name}: 90")
            sld = QSlider(Qt.Horizontal)
            sld.setRange(0, 180)
            sld.setValue(90)
            sld.valueChanged.connect(lambda val, l=lbl, n=name: l.setText(f"{n}: {val}"))
            layout.addWidget(lbl)
            layout.addWidget(sld)
            self.sliders[name] = sld
