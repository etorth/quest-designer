# -*- coding: utf-8 -*-
import sys
from PySide6.QtWidgets import QApplication
from qdmainwindow import QD_MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainWindow = QD_MainWindow()
    mainWindow.show()

    sys.exit(app.exec())