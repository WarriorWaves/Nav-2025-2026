import sys
import os

_TOPSIDE = os.path.dirname(os.path.abspath(__file__))
_GUI     = os.path.join(_TOPSIDE, 'gui_components')
for _p in (_TOPSIDE, _GUI):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame
pygame.init()

from PyQt5.QtWidgets import QApplication
from gui_main import ROVControlPanel

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Warrior Waves ROV")
    window = ROVControlPanel()
    window.showMaximized()

    exit_code = app.exec_()

    pygame.quit()
    sys.exit(exit_code)