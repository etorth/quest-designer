# -*- coding: utf-8 -*-
import sys
from PySide6.QtWidgets import QApplication
from qdmainwindow import QD_MainWindow  # reverted to top-level import

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = QD_MainWindow()
    main_window.show()

    sys.exit(app.exec())