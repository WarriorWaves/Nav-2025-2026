from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSlider
from PyQt5.QtCore import Qt

class ThrusterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.sliders = {}
        for name in ["FR", "FL", "BR", "BL", "F", "B"]:
            lbl = QLabel(f"{name}: 1500")
            sld = QSlider(Qt.Horizontal)
            sld.setRange(1350, 1650)
            sld.setValue(1500)
            sld.valueChanged.connect(lambda val, l=lbl, n=name: l.setText(f"{n}: {val}"))
            layout.addWidget(lbl)
            layout.addWidget(sld)
            self.sliders[name] = sld
