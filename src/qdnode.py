# -*- coding: utf-8 -*-
"""Fundamental quest designer node type.

QD_Node is the base graphics item for all specialized quest nodes.
It provides:
- Rounded rectangle body
- Title text
- Hover + selection visual feedback
- Basic movable/selectable flags

Future extensions can add sockets, I/O ports, custom data, context menus, etc.
"""
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import QRectF, Qt

# Palette constants (centralize for easier theme tweaks)
_NODE_BASE_COLOR = QColor("#272b30")      # Darker than previous #3a3f44
_NODE_BASE_SELECTED = QColor("#2b6fe6")   # Slightly adjusted selection blue
_NODE_BORDER_COLOR = QColor("#222")
_NODE_TEXT_COLOR = QColor("#ffffff")


class QD_Node(QGraphicsObject):
    def __init__(self, title: str = "Node", width: float = 140, height: float = 70, parent=None):
        super().__init__(parent)
        self._title = title
        self._w = width
        self._h = height
        self._hover = False

        # Set interactive flags individually (avoids type checker warning for bitwise OR)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    # --- Required QGraphicsItem interface ---
    def boundingRect(self) -> QRectF:  # noqa: D401
        # Slight margin for pen width
        return QRectF(0, 0, self._w, self._h).adjusted(-1, -1, 1, 1)

    def paint(self, painter: QPainter, option, widget=None):  # noqa: D401
        rect = QRectF(0, 0, self._w, self._h)

        # Base colors (updated palette logic)
        base_color = _NODE_BASE_COLOR
        if self._hover and not self.isSelected():
            # Lighten slightly on hover
            base_color = base_color.lighter(120)
        if self.isSelected():
            base_color = _NODE_BASE_SELECTED

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(_NODE_BORDER_COLOR, 1))
        painter.setBrush(QBrush(base_color))
        painter.drawRoundedRect(rect, 10, 10)

        # Title text
        painter.setPen(_NODE_TEXT_COLOR)
        font: QFont = painter.font()
        font.setBold(True)
        font.setPointSizeF(max(font.pointSizeF() * 0.9, 8))
        painter.setFont(font)
        painter.drawText(rect.adjusted(8, 6, -8, -6), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self._title)

    # --- Hover events ---
    def hoverEnterEvent(self, event):  # noqa: D401
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # noqa: D401
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    # --- Convenience ---
    def setTitle(self, title: str):  # noqa: D401
        self._title = title
        self.update()

    def title(self) -> str:  # noqa: D401
        return self._title

    def size(self):  # noqa: D401
        return self._w, self._h

__all__ = ["QD_Node"]
