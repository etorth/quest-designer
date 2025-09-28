# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QMainWindow, QMenuBar, QApplication
from PySide6.QtGui import QAction  # QAction resides in QtGui in PySide6


class QD_MainWindow(QMainWindow):  # Note: class name as requested
    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_window()
        self._create_menubar()
        self._create_statusbar()

    def _configure_window(self):
        self.setWindowTitle("QuestDesigner")
        self.setMinimumSize(800, 600)

    def _create_menubar(self):
        menubar: QMenuBar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(exit_action)

        # Edit menu (placeholder for future actions)
        menubar.addMenu("&Edit")

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _create_statusbar(self):
        self.statusBar().showMessage("Ready")

    def _show_about_dialog(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About QuestDesigner", "QuestDesigner\nA quest design tool (prototype).")