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
- (NEW) Optional embedded QWidget content via QGraphicsProxyWidget

Future extensions can add sockets, I/O ports, custom data, context menus, etc.
"""
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem, QGraphicsProxyWidget, QWidget  # UPDATED import
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import QRectF, Qt
from typing import List, Optional
from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType  # REVERT to absolute import for script usability

# Palette constants (centralize for easier theme tweaks)
_NODE_BASE_COLOR = QColor("#272b30")      # Darker than previous #3a3f44
_NODE_BASE_SELECTED = QColor("#2b6fe6")   # Slightly adjusted selection blue
_NODE_BORDER_COLOR = QColor("#222")
# NEW: distinct border colors
_NODE_BORDER_HOVER = QColor("#444")
_NODE_BORDER_SELECTED = QColor("#5c9dff")
_NODE_TEXT_COLOR = QColor("#ffffff")

# Layout constants for embedded widget support (NEW)
_TITLE_BAR_HEIGHT = 22  # space reserved for title text
_CONTENT_PADDING = 6    # inner padding around embedded widget


class QD_Node(QGraphicsObject):
    def __init__(self, title: str = "Node", width: float = 140, height: float = 70, parent=None,
                 in_sockets: Optional[List[QD_NodeSocket]] = None,
                 out_sockets: Optional[List[QD_NodeSocket]] = None):
        super().__init__(parent)
        self._title = title
        self._w = width
        self._h = height
        self._hover = False
        # Embedded widget proxy (NEW)
        self._proxy: QGraphicsProxyWidget | None = None
        self._embedded_widget: QWidget | None = None

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

    # --- Socket type policy (NEW) ---------------------------------------
    def default_socket_type(self, direction: SocketDirection):  # noqa: D401
        """Return default SocketType for this node and direction.

        Base QD_Node defaults to DECIMAL for all directions; subclasses may
        override (e.g., state nodes returning BOOL). Specific node classes
        that mix types should construct sockets explicitly with types.
        """
        return SocketType.DECIMAL

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
        # NEW: dynamic border color & thickness
        if self.isSelected():
            border_color = _NODE_BORDER_SELECTED
            border_width = 2
        elif self._hover:
            border_color = _NODE_BORDER_HOVER
            border_width = 1.2
        else:
            border_color = _NODE_BORDER_COLOR
            border_width = 1
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(border_color, border_width))  # UPDATED
        painter.setBrush(QBrush(base_color))
        painter.drawRoundedRect(rect, 10, 10)

        # Title bar area highlight (optional subtle separation) (NEW)
        if self._embedded_widget is not None:
            title_rect = QRectF(0, 0, self._w, _TITLE_BAR_HEIGHT)
            painter.setBrush(QBrush(base_color.darker(110)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(title_rect.adjusted(0, 0, 0, 6), 10, 10)  # slight rounding
            painter.setPen(QPen(border_color, border_width))  # ensure consistent border after title bar

        # Title text
        painter.setPen(_NODE_TEXT_COLOR)
        font: QFont = painter.font()
        font.setBold(True)
        font.setPointSizeF(max(font.pointSizeF() * 0.9, 8))
        painter.setFont(font)
        painter.drawText(QRectF(8, 4, self._w - 16, _TITLE_BAR_HEIGHT - 8),
                         Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, self._title)

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

    # --- Embedded widget support (NEW) ----------------------------------
    def setEmbeddedWidget(self, widget: QWidget | None, auto_resize: bool = True, padding: int = _CONTENT_PADDING):  # noqa: D401
        """Embed (or replace) a QWidget inside the node.

        The widget is wrapped in a QGraphicsProxyWidget and positioned inside
        the node's body below the title bar. If auto_resize is True, the node
        resizes to fit the widget (respecting padding + title bar height).
        Passing None removes any existing embedded widget.
        """
        # Remove previous
        if self._proxy is not None:
            try:
                self.scene().removeItem(self._proxy)
            except Exception:
                pass
            self._proxy = None
            self._embedded_widget = None

        if widget is None:
            self.update()
            return None

        self._embedded_widget = widget
        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(widget)
        # Determine placement rectangle
        y0 = _TITLE_BAR_HEIGHT
        widget.resize(widget.sizeHint())
        wsize = widget.size()
        if auto_resize:
            # Expand node size if widget larger than current interior
            needed_w = wsize.width() + padding * 2
            needed_h = y0 + wsize.height() + padding
            if needed_w > self._w:
                self._w = needed_w
            if needed_h > self._h:
                self._h = needed_h
        x = padding + max(0.0, (self._w - padding * 2 - wsize.width()) / 2.0)
        self._proxy.setPos(x, y0 + padding)
        self.prepareGeometryChange()
        self.update()
        return widget

    def embeddedWidget(self) -> QWidget | None:  # noqa: D401
        return self._embedded_widget

    # --- Socket accessors (NEW) ---
    def input_sockets(self) -> List[QD_NodeSocket]:  # noqa: D401
        return self._in_sockets if self._in_sockets is not None else []

    def output_sockets(self) -> List[QD_NodeSocket]:  # noqa: D401
        return self._out_sockets if self._out_sockets is not None else []

    def add_input_socket(self, socket: QD_NodeSocket | None = None, *, sock_type: SocketType | None = None) -> QD_NodeSocket:
        if self._in_sockets is None:
            self._in_sockets = []
        if socket is None:
            stype: SocketType = sock_type if sock_type is not None else self.default_socket_type(SocketDirection.IN)
            socket = QD_NodeSocket(SocketDirection.IN, self, stype)
        self._in_sockets.append(socket)
        return socket

    def add_output_socket(self, socket: QD_NodeSocket | None = None, *, sock_type: SocketType | None = None) -> QD_NodeSocket:
        if self._out_sockets is None:
            self._out_sockets = []
        if socket is None:
            stype: SocketType = sock_type if sock_type is not None else self.default_socket_type(SocketDirection.OUT)
            socket = QD_NodeSocket(SocketDirection.OUT, self, stype)
        self._out_sockets.append(socket)
        return socket

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
