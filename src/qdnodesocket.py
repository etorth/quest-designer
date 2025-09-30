# -*- coding: utf-8 -*-
"""Node socket graphics item for QuestDesigner.

QD_NodeSocket represents an input or output connection point that can later be
used to attach edges between nodes.

Design goals:
- Lightweight QGraphicsObject (allows future signals / animations)
- Distinguish IN vs OUT via direction enum and color accent
- Hover + selection visual feedback (selection optional for now)
- Easily embeddable inside a QD_Node (parented positioning)
- (NEW) Direction immutable after construction
- (NEW) Parent is mandatory (no orphan sockets)
- (NEW) Track connected edges (single-connection policy currently enforced in scene)
- (NEW) Highlight state for potential targets while connecting
- (UPDATED) Render as a directional half-circle (IN = left half, OUT = right half)
- (NEW) Each socket now has a mandatory data type (DECIMAL, INTEGER, STRING, BOOL)
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Optional, List, TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QPainterPath  # UPDATED imports
from PySide6.QtCore import QRectF, QPointF  # UPDATED import with QPointF

if TYPE_CHECKING:  # avoid runtime import cycle
    from qdedge import QD_Edge

__all__ = ["QD_NodeSocket", "SocketDirection", "SocketType"]


class SocketDirection(Enum):
    IN = auto()
    OUT = auto()


class SocketType(Enum):  # Data type classification for sockets
    DECIMAL = auto()
    INTEGER = auto()
    STRING = auto()
    BOOL = auto()


# Palette (kept subtle to not overpower node visuals)
_SOCKET_FILL_IN = QColor("#3a7f3a")      # greenish for inputs (legacy, kept for reference)
_SOCKET_FILL_OUT = QColor("#9555d6")    # purple for outputs (legacy, kept for reference)
_SOCKET_FILL_HOVER = QColor("#cccccc")   # generic hover overlay (mixed)
_SOCKET_BORDER = QColor("#1c1c1c")
_SOCKET_BORDER_HOVER = QColor("#eeeeee")
_SOCKET_BORDER_HIGHLIGHT = QColor("#ffd866")

# New: per-data-type base colors (chosen for contrast + dark theme comfort)
_SOCKET_TYPE_COLOR = {
    SocketType.DECIMAL: QColor("#4da6ff"),  # calming blue for floating/decimal numbers
    SocketType.INTEGER: QColor("#ffb347"),  # soft orange for ints
    SocketType.STRING:  QColor("#2ecc71"),  # green for textual values
    SocketType.BOOL:    QColor("#c678dd"),  # lavender; shape also differentiates
}


class QD_NodeSocket(QGraphicsObject):
    RADIUS = 6.0
    _TRIANGLE_SCALE = 1.4  # enlargement factor for DECIMAL sockets (triangles)

    def __init__(self, direction: SocketDirection, parent: Optional[QGraphicsObject], sock_type: SocketType = SocketType.DECIMAL):
        if parent is None:
            raise ValueError("QD_NodeSocket requires a non-null parent QGraphicsItem at creation")
        super().__init__(parent)
        self._direction = direction  # immutable after construction
        self._type = sock_type       # immutable data type classification
        self._hover = False
        self._highlight = False
        self._edges: List[QD_Edge] = []  # connections

        # Interaction flags (movable disabled; selection optional)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        # Performance: sockets are tiny; disable geometry notifications
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)

    # --- API --------------------------------------------------------------
    def direction(self) -> SocketDirection:
        return self._direction

    def socket_type(self) -> SocketType:
        return self._type

    def add_edge(self, edge: 'QD_Edge'):
        if edge not in self._edges:
            self._edges.append(edge)

    def remove_edge(self, edge: 'QD_Edge'):
        if edge in self._edges:
            self._edges.remove(edge)

    def edges(self) -> List['QD_Edge']:
        return list(self._edges)

    def is_occupied(self) -> bool:
        return len(self._edges) > 0

    def set_highlight(self, flag: bool):
        if self._highlight != flag:
            self._highlight = flag
            self.update()

    # --- QGraphicsItem overrides -----------------------------------------
    def boundingRect(self) -> QRectF:  # noqa: D401
        r = self.RADIUS
        # Expand bounding rect for enlarged triangle sockets
        if self._type == SocketType.DECIMAL:
            scale = self._TRIANGLE_SCALE
            if self._direction == SocketDirection.IN:
                left = -r * scale
                right = r  # keep right side at original center-to-right extent
            else:  # OUT
                left = -r
                right = r * scale
            return QRectF(left, -r, right - left, 2 * r)
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):  # noqa: D401
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Base fill determined by socket data type now (instead of direction)
        fill = _SOCKET_TYPE_COLOR.get(self._type, QColor("#666666"))
        # Subtle direction cue: darken inputs a bit, lighten outputs a bit
        if self._direction == SocketDirection.IN:
            fill = fill.darker(110)
        else:
            fill = fill.lighter(110)
        if self._highlight:
            fill = fill.lighter(135)
        if self._hover:
            fill = fill.lighter(125)
        if self.isSelected():
            fill = fill.lighter(140)

        if self._highlight:
            pen_color = _SOCKET_BORDER_HIGHLIGHT
        else:
            pen_color = _SOCKET_BORDER_HOVER if (self._hover or self.isSelected()) else _SOCKET_BORDER
        pen = QPen(pen_color, 1)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill))

        rect = self.boundingRect()
        r = self.RADIUS
        # BOOL sockets: draw half-square instead of half-circle
        if self._type == SocketType.BOOL:
            if self._direction == SocketDirection.IN:
                half_rect = QRectF(-r, -r, r, 2 * r)  # left half
            else:
                half_rect = QRectF(0, -r, r, 2 * r)   # right half
            painter.drawRect(half_rect)
            return
        # DECIMAL sockets: enlarged directional triangle
        if self._type == SocketType.DECIMAL:
            scale = self._TRIANGLE_SCALE
            if self._direction == SocketDirection.IN:
                points = [QPointF(0, -r), QPointF(-r * scale, 0), QPointF(0, r)]
            else:
                points = [QPointF(0, -r), QPointF(r * scale, 0), QPointF(0, r)]
            poly = QPolygonF(points)
            painter.drawPolygon(poly)
            return

        # Other types (INTEGER, STRING): draw half-circle (existing behavior)
        if self._direction == SocketDirection.IN:
            # Left half: from 90° to 270° (span 180°)
            start = 90 * 16
            span = 180 * 16
        else:  # OUT
            # Right half: from 270° to 90° (span 180°)
            start = 270 * 16
            span = 180 * 16
        painter.drawPie(rect, start, span)

    def shape(self):  # noqa: D401
        path = QPainterPath()
        rect = self.boundingRect()
        r = self.RADIUS
        if self._type == SocketType.BOOL:
            if self._direction == SocketDirection.IN:
                path.addRect(QRectF(-r, -r, r, 2 * r))
            else:
                path.addRect(QRectF(0, -r, r, 2 * r))
            return path
        if self._type == SocketType.DECIMAL:
            scale = self._TRIANGLE_SCALE
            if self._direction == SocketDirection.IN:
                path.moveTo(0, -r)
                path.lineTo(-r * scale, 0)
                path.lineTo(0, r)
            else:
                path.moveTo(0, -r)
                path.lineTo(r * scale, 0)
                path.lineTo(0, r)
            path.closeSubpath()
            return path
        if self._direction == SocketDirection.IN:
            # Left half-circle
            start = 90 * 16
            span = 180 * 16
        else:
            # Right half-circle
            start = 270 * 16
            span = 180 * 16
        start_deg = start / 16.0
        span_deg = span / 16.0
        path.moveTo(0, 0)
        path.arcMoveTo(rect, start_deg)
        path.arcTo(rect, start_deg, span_deg)
        path.closeSubpath()
        return path

    # --- Hover events -----------------------------------------------------
    def hoverEnterEvent(self, event):  # noqa: D401
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # noqa: D401
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    # --- Optional convenience --------------------------------------------
    def radius(self) -> float:  # noqa: D401
        return self.RADIUS

    def __repr__(self) -> str:  # noqa: D401
        return f"<QD_NodeSocket dir={self._direction.name} type={self._type.name} occupied={self.is_occupied()}>"
