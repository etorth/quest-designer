# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QApplication, QMdiArea, QLabel
)
from PySide6.QtGui import QAction
from qdmdiwindow import QD_MdiWindow
from qdstatewindow import QD_StateWindow
from PySide6.QtCore import Qt
from qdgfxview import QD_GfxView  # NEW import for isinstance check


class QD_MainWindow(QMainWindow):  # Note: class name as requested
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mdi_seq = 1  # sequence counter for new subwindows
        self._zoom_label: QLabel | None = None
        self._configure_window()
        self._create_menubar()
        self._create_statusbar()
        self._create_mdi_area()
        self.mdi_area.subWindowActivated.connect(self._on_subwindow_activated)

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

        # View menu (zoom controls)
        view_menu = menubar.addMenu("&View")

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl+=")  # also handles Ctrl+ since + often requires Shift
        zoom_in_action.setStatusTip("Zoom in (Ctrl + Wheel)")
        zoom_in_action.triggered.connect(self._action_zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.setStatusTip("Zoom out (Ctrl + Wheel)")
        zoom_out_action.triggered.connect(self._action_zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.setStatusTip("Reset zoom to 100%")
        reset_zoom_action.triggered.connect(self._action_reset_zoom)
        view_menu.addAction(reset_zoom_action)

        fit_scene_action = QAction("Fit &Scene", self)
        fit_scene_action.setShortcut("Ctrl+Shift+F")
        fit_scene_action.setStatusTip("Fit entire scene into view")
        fit_scene_action.triggered.connect(self._action_fit_scene)
        view_menu.addAction(fit_scene_action)

        # Edit menu (placeholder for future actions)
        menubar.addMenu("&Edit")

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _create_statusbar(self):
        bar = self.statusBar()
        bar.showMessage("Ready")
        self._zoom_label = QLabel("Zoom: -")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bar.addPermanentWidget(self._zoom_label)

    # --- Project action handlers ---
    def _new_project(self):
        mdi = QD_StateWindow(title=f"Scene {self._mdi_seq}")
        self._mdi_seq += 1
        self.mdi_area.addSubWindow(mdi)
        # Connect zoom signal (guarded)
        try:
            view = mdi.graphics_view()
            if isinstance(view, QD_GfxView):
                view.zoomChanged.connect(lambda _s, wref=mdi: self._update_zoom_label_from_mdi(wref))
        except Exception:  # pragma: no cover - defensive
            pass
        mdi.show()
        self.statusBar().showMessage("Created new graphics scene window", 3000)
        self._update_zoom_label_from_mdi(mdi)

    def _open_project(self):
        self.statusBar().showMessage("Open project (not yet implemented)", 3000)

    def _save_project(self):
        active = self.mdi_area.activeSubWindow()
        if not isinstance(active, QD_MdiWindow):
            self.statusBar().showMessage("No active window to save", 3000)
            return
        self.statusBar().showMessage(f"Saved '{active.windowTitle()}' (not actually implemented)", 3000)

    def _show_about_dialog(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About QuestDesigner", "QuestDesigner\nA quest design tool (prototype).")

    # --- View action handlers ---
    def _get_active_mdi(self) -> QD_MdiWindow | None:
        sub = self.mdi_area.activeSubWindow()
        if isinstance(sub, QD_MdiWindow):
            return sub
        return None

    def _action_zoom_in(self):
        mdi = self._get_active_mdi()
        if mdi:
            mdi.zoom_in()
            self._update_zoom_label_from_mdi(mdi)

    def _action_zoom_out(self):
        mdi = self._get_active_mdi()
        if mdi:
            mdi.zoom_out()
            self._update_zoom_label_from_mdi(mdi)

    def _action_reset_zoom(self):
        mdi = self._get_active_mdi()
        if mdi:
            mdi.reset_zoom()
            self._update_zoom_label_from_mdi(mdi)

    def _action_fit_scene(self):
        mdi = self._get_active_mdi()
        if mdi:
            mdi.fit_scene()
            self._update_zoom_label_from_mdi(mdi)

    # --- Zoom label maintenance ---
    def _update_zoom_label_from_mdi(self, mdi: QD_MdiWindow | None):
        if not self._zoom_label:
            return
        if mdi is None:
            self._zoom_label.setText("Zoom: -")
            return
        try:
            percent = mdi.current_zoom_percent()
            self._zoom_label.setText(f"Zoom: {percent}%")
        except Exception:  # pragma: no cover
            self._zoom_label.setText("Zoom: ?")

    def _on_subwindow_activated(self, mdi):
        if isinstance(mdi, QD_MdiWindow):
            self._update_zoom_label_from_mdi(mdi)
        else:
            self._update_zoom_label_from_mdi(None)
