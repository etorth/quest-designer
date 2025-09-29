# -*- coding: utf-8 -*-
"""MDI subwindow implementation for QuestDesigner.

QD_MdiWindow encapsulates a QGraphicsScene + QGraphicsView pair prepared for
future quest node / edge graphics items.
"""
from PySide6.QtWidgets import QMdiSubWindow, QGraphicsView
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt
from qdnode import QD_Node  # Added import
from gdgfxscene import QD_GfxScene  # NEW: custom graphics scene


class QD_MdiWindow(QMdiSubWindow):
    def __init__(self, title: str | None = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._init_scene_view()
        self._add_demo_node()  # Add demo node
        if title:
            self.setWindowTitle(title)

    # --- Initialization helpers ---
    def _init_scene_view(self):
        # Use custom scene class instead of raw QGraphicsScene
        self.scene = QD_GfxScene(self)
        self.view = QGraphicsView(self.scene)
        self._configure_view()
        self.setWidget(self.view)

    def _configure_view(self):
        v = self.view
        v.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        v.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        v.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        v.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        v.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def _add_demo_node(self):
        """Create and place a demo QD_Node in the center of the scene."""
        node = QD_Node(title="Demo Node")
        w, h = node.size()
        node.setPos(-w / 2, -h / 2)  # Center the node roughly at scene origin
        self.scene.addItem(node)

    # --- Optional utilities ---
    def add_demo_grid(self, step: int = 50, extent: int = 500, color: str = "#888"):
        """Draw a lightweight grid. Call manually if desired.

        NOTE: QD_GfxScene already draws a background grid; this method remains
        for experimentation (adds grid as items instead of background paint).
        """
        from PySide6.QtWidgets import QGraphicsLineItem
        pen = QPen(QColor(color))
        for x in range(-extent, extent + 1, step):
            line = QGraphicsLineItem(x, -extent, x, extent)
            line.setPen(pen)
            self.scene.addItem(line)
        for y in range(-extent, extent + 1, step):
            line = QGraphicsLineItem(-extent, y, extent, y)
            line.setPen(pen)
            self.scene.addItem(line)

    # Public accessors (optional convenience)
    def graphics_scene(self) -> QD_GfxScene:  # noqa: D401
        """Return the underlying QD_GfxScene."""
        return self.scene

    def graphics_view(self) -> QGraphicsView:  # noqa: D401
        """Return the underlying QGraphicsView."""
        return self.view

__all__ = ["QD_MdiWindow"]
