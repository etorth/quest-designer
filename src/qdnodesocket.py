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
from PySide6.QtCore import Qt, QRectF, QPointF  # UPDATED import with QPointF

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
    _TRIANGLE_SCALE = 1.4  # retained (unused now) for potential future scaling

    TYPE_LABELS = {
        SocketType.INTEGER: "I",
        SocketType.STRING: "S",
        SocketType.BOOL: "B",
        SocketType.DECIMAL: "D",
    }

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
        # Unified square bounding box
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):  # noqa: D401
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Base color by data type
        fill = _SOCKET_TYPE_COLOR.get(self._type, QColor("#666666"))
        # Direction cue (optional): darken IN, lighten OUT
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
        painter.drawRect(rect)

        # Draw type label centered (always black font per request)
        label = self.TYPE_LABELS.get(self._type, "?")
        painter.setPen(QColor("#000000"))
        font = painter.font()
        font.setBold(False)
        font.setPointSizeF(max(6.0, self.RADIUS * 1.6))
        painter.setFont(font)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), label)

    def shape(self):  # noqa: D401
        # Square shape for hit detection
        path = QPainterPath()
        path.addRect(self.boundingRect())
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
