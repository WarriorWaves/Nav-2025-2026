import sys
import os

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gui_components'))

from gui_main import ROVControlPanel

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Warrior Waves ROV")
    window = ROVControlPanel()
    window.showMaximized()
    sys.exit(app.exec_())