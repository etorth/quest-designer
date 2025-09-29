# -*- coding: utf-8 -*-
"""MDI subwindow implementation for QuestDesigner.

QD_MdiWindow encapsulates a QGraphicsScene + QGraphicsView pair prepared for
future quest node / edge graphics items.
"""
from PySide6.QtWidgets import QMdiSubWindow, QGraphicsView
from PySide6.QtCore import Qt
from qdgfxscene import QD_GfxScene  # renamed from gdgfxscene
from qdgfxview import QD_GfxView  # NEW: custom zoom-capable view


class QD_MdiWindow(QMdiSubWindow):
    def __init__(self, title: str | None = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._init_scene_view()
        if title:
            self.setWindowTitle(title)

    # --- Initialization helpers ---
    def _init_scene_view(self):
        # Use custom scene class instead of raw QGraphicsScene
        self.scene = QD_GfxScene(self)
        # Replace generic QGraphicsView with QD_GfxView (adds zoom features)
        self.view = QD_GfxView(self.scene)
        self.setWidget(self.view)

    # --- Zoom convenience (delegates to QD_GfxView) ---
    def zoom_in(self):
        self.view.zoom_in()

    def zoom_out(self):
        self.view.zoom_out()

    def reset_zoom(self):
        self.view.reset_zoom()

    def fit_scene(self):
        self.view.fit_scene()

    def current_zoom_percent(self) -> int:
        scale = self.view.transform().m11()
        return int(round(scale * 100))

    # Public accessors (optional convenience)
    def graphics_scene(self) -> QD_GfxScene:  # noqa: D401
        """Return the underlying QD_GfxScene."""
        return self.scene

    def graphics_view(self) -> QGraphicsView:  # noqa: D401
        """Return the underlying QGraphicsView."""
        return self.view

__all__ = ["QD_MdiWindow"]
