# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QApplication, QMdiArea
)
from PySide6.QtGui import QAction
from qdmdiwindow import QD_MdiWindow


class QD_MainWindow(QMainWindow):  # Note: class name as requested
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mdi_seq = 1  # sequence counter for new subwindows
        self._configure_window()
        self._create_menubar()
        self._create_statusbar()
        self._create_mdi_area()

    def _configure_window(self):
        self.setWindowTitle("QuestDesigner")
        self.setMinimumSize(800, 600)

    def _create_mdi_area(self):
        # Central MDI area starts empty
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)

    def _create_menubar(self):
        menubar: QMenuBar = self.menuBar()

        # Project menu (replaces former File menu)
        project_menu = menubar.addMenu("&Project")

        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new project window")
        new_action.triggered.connect(self._new_project)
        project_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(self._open_project)
        project_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save current project")
        save_action.triggered.connect(self._save_project)
        project_menu.addAction(save_action)

        project_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(QApplication.instance().quit)
        project_menu.addAction(exit_action)

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

    # --- Project action handlers ---
    def _new_project(self):
        mdi = QD_MdiWindow(title=f"Scene {self._mdi_seq}")
        self._mdi_seq += 1
        self.mdi_area.addSubWindow(mdi)
        mdi.show()
        self.statusBar().showMessage("Created new graphics scene window", 3000)

    def _open_project(self):
        self.statusBar().showMessage("Open project (not yet implemented)", 3000)

    def _save_project(self):
        active = self.mdi_area.activeSubWindow()
        if active is None:
            self.statusBar().showMessage("No active window to save", 3000)
            return
        # Placeholder save logic
        self.statusBar().showMessage(f"Saved '{active.windowTitle()}' (not actually implemented)", 3000)

    def _show_about_dialog(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About QuestDesigner", "QuestDesigner\nA quest design tool (prototype).")