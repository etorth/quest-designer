# -*- coding: utf-8 -*-
"""Node socket graphics item for QuestDesigner.

QD_NodeSocket represents an input or output connection point that can later be
used to attach edges between nodes.

Design goals:
- Lightweight QGraphicsObject (allows future signals / animations)
- Distinguish IN vs OUT via direction enum and color accent
- Hover + selection visual feedback (selection optional for now)
- Easily embeddable inside a QD_Node (parented positioning)
- Direction immutable after construction
- Parent is mandatory (no orphan sockets)
- Track connected edges (single-connection policy currently enforced in scene)
- Highlight state for potential targets while connecting
- Each socket now has a mandatory data type (DECIMAL, INTEGER, STRING, BOOL)
- NEW: Data type is now mutable post-construction (direction stays immutable)

(Refactored: all project-local APIs now snake_case. Kept Qt override names.)
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Optional, List, TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF

if TYPE_CHECKING:  # avoid runtime import cycle
    from qdedge import QD_Edge

__all__ = ["QD_NodeSocket", "SocketDirection", "SocketType", "socket_data_type_match"]


class SocketDirection(Enum):
    IN = auto()
    OUT = auto()


class SocketType(Enum):  # Data type classification for sockets
    DECIMAL = auto()
    INTEGER = auto()
    STRING = auto()
    BOOL = auto()
    PROCESS = auto()  # NEW: process/control flow socket


# --- Data type compatibility policy ---------------------------------------
# Rules (OUT -> IN):
# - STRING   -> STRING only
# - BOOL     -> BOOL only
# - PROCESS  -> PROCESS only (control flow links)
# - INTEGER  -> INTEGER or DECIMAL (widen)
# - DECIMAL  -> DECIMAL only (no implicit narrowing to INTEGER)
# (Extendable for future coercions.)

def socket_data_type_match(out_socket: "QD_NodeSocket", in_socket: "QD_NodeSocket") -> bool:
    """Return True if data types are compatible for a connection OUT -> IN.

    Caller must ensure direction ordering (out_socket is OUT, in_socket is IN).
    This function enforces strict (or widening) compatibility without implicit
    narrowing conversions.
    """
    t_out = out_socket.socket_type()
    t_in = in_socket.socket_type()
    if t_out == SocketType.STRING:
        return t_in == SocketType.STRING
    if t_out == SocketType.BOOL:
        return t_in == SocketType.BOOL
    if t_out == SocketType.PROCESS:
        return t_in == SocketType.PROCESS
    if t_out == SocketType.INTEGER:
        return t_in in (SocketType.INTEGER, SocketType.DECIMAL)
    if t_out == SocketType.DECIMAL:
        return t_in == SocketType.DECIMAL
    return False


# Palette
_SOCKET_BORDER = QColor("#1c1c1c")
_SOCKET_BORDER_HOVER = QColor("#eeeeee")
_SOCKET_BORDER_HIGHLIGHT = QColor("#ffd866")

_SOCKET_TYPE_COLOR = {
    SocketType.DECIMAL: QColor("#4da6ff"),
    SocketType.INTEGER: QColor("#ffb347"),
    SocketType.STRING: QColor("#2ecc71"),
    SocketType.BOOL: QColor("#c678dd"),
    SocketType.PROCESS: QColor("#ffd700"),  # NEW distinct golden color
}


class QD_NodeSocket(QGraphicsObject):
    RADIUS = 6.0

    TYPE_LABELS = {
        SocketType.INTEGER: "I",
        SocketType.STRING: "S",
        SocketType.BOOL: "B",
        SocketType.DECIMAL: "D",
        SocketType.PROCESS: "P",  # NEW label
    }

    def __init__(self, direction: SocketDirection, parent: Optional[QGraphicsObject], sock_type: SocketType = SocketType.DECIMAL):
        if parent is None:
            raise ValueError("QD_NodeSocket requires a non-null parent QGraphicsItem at creation")
        super().__init__(parent)
        self._direction = direction  # immutable
        self._type = sock_type       # immutable
        self._hover = False
        self._highlight = False
        self._edges: List[QD_Edge] = []

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)

    # --- API --------------------------------------------------------------
    def direction(self) -> SocketDirection:  # kept (simple lowercase)
        return self._direction

    def socket_type(self) -> SocketType:
        return self._type

    def set_socket_type(self, new_type: SocketType, detach_incompatible: bool = True):  # NEW mutator
        """Set (mutate) the socket's data type.

        If detach_incompatible is True, any connected edges that become
        incompatible under OUT->IN compatibility rules are removed from the
        scene (or detached safely if scene missing).
        """
        if new_type == self._type:
            return
        self._type = new_type
        if detach_incompatible and self._edges:
            # Collect edges first to avoid mutation during iteration
            to_check = list(self._edges)
            for edge in to_check:
                try:
                    other = None
                    # Determine counterpart socket
                    if edge.begin_socket() is self:
                        other = edge.end_socket()
                    elif edge.end_socket() is self:
                        other = edge.begin_socket()
                    # If counterpart missing, just continue (edge is half-connected)
                    if other is None:
                        # Half-connected edge: allow type change; visual update only
                        edge.update()
                        continue
                    # Need one OUT and one IN to evaluate compatibility
                    if self.direction() == other.direction():
                        # Invalid orientation pair; drop edge
                        if edge.scene():
                            edge.scene().removeItem(edge)
                        else:
                            edge.detach()
                        continue
                    # Determine OUT/IN ordering for compatibility test
                    if self.direction() == SocketDirection.OUT:
                        out_sock, in_sock = self, other
                    else:
                        out_sock, in_sock = other, self
                    if not socket_data_type_match(out_sock, in_sock):
                        # Incompatible now: remove
                        if edge.scene():
                            edge.scene().removeItem(edge)
                        else:
                            edge.detach()
                    else:
                        # Still compatible; just refresh visuals
                        edge.update()
                except Exception:
                    # Best-effort cleanup
                    try:
                        if edge.scene():
                            edge.scene().removeItem(edge)
                    except Exception:
                        pass
        self.update()

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

    def connection_point(self) -> QPointF:
        """Return the scene position where an edge should attach.

        OUT socket: midpoint of right edge of the square
        IN socket:  midpoint of left  edge of the square
        (Fallback: center)
        """
        center = self.scenePos()
        if self._direction == SocketDirection.OUT:
            return QPointF(center.x() + self.RADIUS, center.y())
        if self._direction == SocketDirection.IN:
            return QPointF(center.x() - self.RADIUS, center.y())
        return center

    # --- QGraphicsItem overrides -----------------------------------------
    def boundingRect(self) -> QRectF:  # Qt override (keep camel)
        r = self.RADIUS
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):  # Qt override
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        fill = _SOCKET_TYPE_COLOR.get(self._type, QColor("#666666"))
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
        # Glow (option B): show on any hover; amplified when highlighted
        if self._hover or self._highlight:
            glow_color = QColor(fill)
            # Base alpha
            base_alpha = 70
            if self._highlight:
                base_alpha = 130
            if self.isSelected():
                base_alpha = min(200, base_alpha + 40)
            glow_color.setAlpha(base_alpha)
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            # Slightly larger rect for glow halo
            r = self.RADIUS + 3
            painter.drawRoundedRect(QRectF(-r, -r, 2 * r, 2 * r), 3, 3)
            painter.restore()
        pen_color = _SOCKET_BORDER_HIGHLIGHT if self._highlight else (_SOCKET_BORDER_HOVER if (self._hover or self.isSelected()) else _SOCKET_BORDER)
        painter.setPen(QPen(pen_color, 1))
        painter.setBrush(QBrush(fill))
        rect = self.boundingRect()
        painter.drawRect(rect)
        label = self.TYPE_LABELS.get(self._type, "?")
        painter.setPen(QColor("#000000"))
        font = painter.font()
        font.setBold(False)
        font.setPointSizeF(max(6.0, self.RADIUS * 1.5))
        painter.setFont(font)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), label)

    def shape(self):  # Qt override
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    # --- Hover events -----------------------------------------------------
    def hoverEnterEvent(self, event):  # Qt override
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # Qt override
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    # --- Misc -------------------------------------------------------------
    def radius(self) -> float:
        return self.RADIUS

    def __repr__(self) -> str:
        return f"<QD_NodeSocket dir={self._direction.name} type={self._type.name} occupied={self.is_occupied()}>"
