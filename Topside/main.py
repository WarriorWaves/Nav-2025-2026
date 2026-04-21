import sys
import os

_TOPSIDE = os.path.dirname(os.path.abspath(__file__))
if _TOPSIDE not in sys.path:
    sys.path.insert(0, _TOPSIDE)

_GUI = os.path.join(_TOPSIDE, 'gui_components')
if _GUI not in sys.path:
    sys.path.insert(0, _GUI)

from PyQt5.QtWidgets import QApplication
from gui_main import ROVControlPanel

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Warrior Waves ROV")
    window = ROVControlPanel()
    window.showMaximized()
    sys.exit(app.exec_())