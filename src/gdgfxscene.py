# -*- coding: utf-8 -*-
"""Graphics scene implementation for QuestDesigner.

QD_GfxScene centralizes custom rendering / behaviors (grid, future snapping,
context menus, selection helpers, etc.). QD_MdiWindow uses this instead of a
plain QGraphicsScene so later enhancements remain localized here.
"""

from typing import Optional
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import QRectF


class QD_GfxScene(QGraphicsScene):
    DEFAULT_RECT = (-2000, -2000, 4000, 4000)
    # --- Color palette (tweakable) ---
    _BG_COLOR = QColor(0x2f, 0x31, 0x36)          # Neutral dark grey (comfortable, low contrast)
    _GRID_MINOR = QColor(0x3b, 0x3e, 0x44)        # Subtle minor lines
    _GRID_MAJOR = QColor(0x4a, 0x4f, 0x55)        # Slightly brighter major lines

    def __init__(self, parent=None, scene_rect: Optional[QRectF] = None, grid_step: int = 50):
        # Initialize base scene rectangle (mirrors previous hard‑coded values)
        if scene_rect is None:
            x, y, w, h = self.DEFAULT_RECT
            super().__init__(x, y, w, h, parent)
        else:
            super().__init__(scene_rect, parent)
        self._grid_step = grid_step
        # Disable indexing for potentially dynamic many-item scenes (faster inserts)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

    # --- Configuration API -------------------------------------------------
    def set_grid_step(self, step: int):
        self._grid_step = max(5, step)
        self.update()  # trigger redraw

    def grid_step(self) -> int:
        return self._grid_step

    # --- Drawing ------------------------------------------------------------
    def drawBackground(self, painter: QPainter, rect: QRectF):  # noqa: N802 (Qt naming)
        """Draw a lightweight infinite grid with a soft dark background.

        Major lines every 5 steps are slightly brighter for orientation.
        """
        # Background fill (do BEFORE calling base implementation)
        painter.fillRect(rect, self._BG_COLOR)

        step = self._grid_step
        if step <= 0:
            return

        # Prepare pens once
        minor_pen = QPen(self._GRID_MINOR)
        major_pen = QPen(self._GRID_MAJOR)
        for p in (minor_pen, major_pen):
            p.setWidthF(0)  # cosmetic, 1px regardless of zoom

        # Align starting coordinates to grid
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)
        right = int(rect.right())
        bottom = int(rect.bottom())

        # Vertical lines
        x = left
        top_i = int(rect.top())
        bottom_i = int(rect.bottom())
        while x <= right:
            index = int(round(x / step))
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            painter.drawLine(int(x), top_i, int(x), bottom_i)
            x += step

        # Horizontal lines
        y = top
        left_i = int(rect.left())
        right_i = int(rect.right())
        while y <= bottom:
            index = int(round(y / step))
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            painter.drawLine(left_i, int(y), right_i, int(y))
            y += step

__all__ = ["QD_GfxScene"]
