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
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Optional, List, TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtCore import QRectF, Qt, QPointF  # added QPointF

if TYPE_CHECKING:  # avoid runtime import cycle
    from qdedge import QD_Edge

__all__ = ["QD_NodeSocket", "SocketDirection"]


class SocketDirection(Enum):
    IN = auto()
    OUT = auto()


# Palette (kept subtle to not overpower node visuals)
_SOCKET_FILL_IN = QColor("#3a7f3a")      # greenish for inputs
_SOCKET_FILL_OUT = QColor("#9555d6")    # purple for outputs
_SOCKET_FILL_HOVER = QColor("#cccccc")   # generic hover overlay (mixed)
_SOCKET_BORDER = QColor("#1c1c1c")
_SOCKET_BORDER_HOVER = QColor("#eeeeee")
_SOCKET_BORDER_HIGHLIGHT = QColor("#ffd866")


class QD_NodeSocket(QGraphicsObject):
    RADIUS = 6.0

    def __init__(self, direction: SocketDirection, parent: Optional[QGraphicsItem]):
        if parent is None:
            raise ValueError("QD_NodeSocket requires a non-null parent QGraphicsItem at creation")
        super().__init__(parent)
        self._direction = direction  # immutable after construction
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
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):  # noqa: D401
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        fill = _SOCKET_FILL_IN if self._direction == SocketDirection.IN else _SOCKET_FILL_OUT
        if self._highlight:
            fill = fill.lighter(135)
        if self._hover:
            fill = fill.lighter(130)
        if self.isSelected():
            fill = fill.lighter(150)

        if self._highlight:
            pen_color = _SOCKET_BORDER_HIGHLIGHT
        else:
            pen_color = _SOCKET_BORDER_HOVER if (self._hover or self.isSelected()) else _SOCKET_BORDER
        pen = QPen(pen_color, 1)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill))

        rect = self.boundingRect()
        # QPainter angles: 0 at 3 o'clock, positive CCW; specify in 1/16 deg
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
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        rect = self.boundingRect()
        if self._direction == SocketDirection.IN:
            start = 90 * 16
            span = 180 * 16
        else:
            start = 270 * 16
            span = 180 * 16
        # Build half-circle path using arcTo
        # arcTo expects: x, y, w, h, startAngle(deg), sweepLength(deg)
        # Convert from 1/16 deg values
        start_deg = start / 16.0
        span_deg = span / 16.0
        path.moveTo(0, 0)  # center reference (optional for hit area)
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

