# -*- coding: utf-8 -*-
"""Fundamental quest designer node type.

QD_Node is the base graphics item for all specialized quest nodes.
It provides:
- Rounded rectangle body
- Title text
- Hover + selection visual feedback
- Basic movable/selectable flags
- (NEW) Lists of input/output sockets (may be empty or None)
- (NEW) Validation of provided socket direction lists
- (NEW) Edge path refresh when node position changes

Future extensions can add sockets, I/O ports, custom data, context menus, etc.
"""
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import QRectF, Qt
from typing import List, Optional
from qdnodesocket import QD_NodeSocket, SocketDirection  # NEW import

# Palette constants (centralize for easier theme tweaks)
_NODE_BASE_COLOR = QColor("#272b30")      # Darker than previous #3a3f44
_NODE_BASE_SELECTED = QColor("#2b6fe6")   # Slightly adjusted selection blue
_NODE_BORDER_COLOR = QColor("#222")
_NODE_TEXT_COLOR = QColor("#ffffff")


class QD_Node(QGraphicsObject):
    def __init__(self, title: str = "Node", width: float = 140, height: float = 70, parent=None,
                 in_sockets: Optional[List[QD_NodeSocket]] = None,
                 out_sockets: Optional[List[QD_NodeSocket]] = None):
        super().__init__(parent)
        self._title = title
        self._w = width
        self._h = height
        self._hover = False

        # --- Validate provided sockets (if any) ---
        if in_sockets is not None:
            for sock in in_sockets:
                if not isinstance(sock, QD_NodeSocket):
                    raise ValueError(f"in_sockets contains non-QD_NodeSocket: {sock!r}")
                if sock.direction() != SocketDirection.IN:
                    raise ValueError("in_sockets contains a socket that is not IN direction")
        if out_sockets is not None:
            for sock in out_sockets:
                if not isinstance(sock, QD_NodeSocket):
                    raise ValueError(f"out_sockets contains non-QD_NodeSocket: {sock!r}")
                if sock.direction() != SocketDirection.OUT:
                    raise ValueError("out_sockets contains a socket that is not OUT direction")

        # NEW socket containers (may be None or list). Use exactly what caller passes after validation.
        self._in_sockets: Optional[List[QD_NodeSocket]] = in_sockets if in_sockets is not None else []
        self._out_sockets: Optional[List[QD_NodeSocket]] = out_sockets if out_sockets is not None else []

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

    # --- Socket accessors (NEW) ---
    def input_sockets(self) -> List[QD_NodeSocket]:  # noqa: D401
        return self._in_sockets if self._in_sockets is not None else []

    def output_sockets(self) -> List[QD_NodeSocket]:  # noqa: D401
        return self._out_sockets if self._out_sockets is not None else []

    def add_input_socket(self, socket: QD_NodeSocket | None = None) -> QD_NodeSocket:
        if self._in_sockets is None:
            self._in_sockets = []
        sock = socket or QD_NodeSocket(SocketDirection.IN, parent=self)
        self._in_sockets.append(sock)
        return sock

    def add_output_socket(self, socket: QD_NodeSocket | None = None) -> QD_NodeSocket:
        if self._out_sockets is None:
            self._out_sockets = []
        sock = socket or QD_NodeSocket(SocketDirection.OUT, parent=self)
        self._out_sockets.append(sock)
        return sock

    def itemChange(self, change, value):  # noqa: D401
        try:
            if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
                # Update all connected edge paths since socket positions shifted
                for sock in (self._in_sockets or []):
                    for edge in sock.edges():
                        edge.update_path()
                for sock in (self._out_sockets or []):
                    for edge in sock.edges():
                        edge.update_path()
        except Exception:  # pragma: no cover - defensive
            pass
        return super().itemChange(change, value)

__all__ = ["QD_Node"]
