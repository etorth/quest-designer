# -*- coding: utf-8 -*-
"""Fundamental quest designer node type (refactored to snake_case APIs)."""
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem, QGraphicsProxyWidget, QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import QRectF, Qt, QEvent
from typing import List, Optional
from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType

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
_MIN_NODE_WIDTH = 120   # NEW: basic safety minimum
_MIN_NODE_HEIGHT = 50   # NEW: basic safety minimum (excluding widget growth)
_RESIZE_MARGIN = 6      # NEW: pixel margin for edge resize detection


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
        # Track last fitted size to avoid redundant geometry changes (NEW)
        self._last_fit_w = self._w
        self._last_fit_h = self._h
        # --- Resize interaction state (NEW) ---
        self._resizing = False
        self._resize_left = False
        self._resize_right = False
        self._resize_top = False
        self._resize_bottom = False
        self._resize_origin_scene = None
        self._orig_rect = None  # (x, y, w, h)

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

    # --- Socket type policy ----------------------------------------------
    def default_socket_type(self, direction: SocketDirection):
        """Return default SocketType for this node and direction.

        Base QD_Node defaults to DECIMAL for all directions; subclasses may
        override (e.g., state nodes returning BOOL). Specific node classes
        that mix types should construct sockets explicitly with types.
        """
        return SocketType.DECIMAL

    # --- QGraphicsItem interface -----------------------------------------
    def boundingRect(self) -> QRectF:  # Qt override keep camelCase
        # Slight margin for pen width
        return QRectF(0, 0, self._w, self._h).adjusted(-1, -1, 1, 1)

    def paint(self, painter: QPainter, option, widget=None):  # Qt override
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

    # --- Hover events -----------------------------------------------------
    def hoverEnterEvent(self, event):  # Qt override
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # Qt override
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    # --- Convenience ------------------------------------------------------
    def set_title(self, title: str):  # noqa: D401
        self._title = title
        self.update()

    def title(self) -> str:  # keep for external display
        return self._title

    def size(self):  # noqa: D401
        return self._w, self._h

    # --- Embedded widget support -----------------------------------------
    def set_embedded_widget(self, widget: QWidget | None, auto_resize: bool = True, padding: int = _CONTENT_PADDING):  # noqa: D401
        """Embed (or replace) a QWidget inside the node.
        Ensures node always at least large enough to contain widget + padding.
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
        try:
            widget.installEventFilter(self)  # monitor size/layout changes
        except Exception:
            pass
        widget.resize(widget.sizeHint())
        if auto_resize:
            self._fit_node_to_widget(padding)
        else:
            self._center_embedded_widget_in_body(padding)
        self.update()
        return widget

    def _fit_node_to_widget(self, padding: int = _CONTENT_PADDING):  # NEW
        if not self._embedded_widget:
            return
        w_hint = max(self._embedded_widget.sizeHint().width(), self._embedded_widget.width())
        h_hint = max(self._embedded_widget.sizeHint().height(), self._embedded_widget.height())
        needed_w = max(_MIN_NODE_WIDTH, w_hint + padding * 2)
        needed_h = max(_MIN_NODE_HEIGHT, _TITLE_BAR_HEIGHT + h_hint + padding)
        if needed_w != self._w or needed_h != self._h:
            try:
                self.prepareGeometryChange()
            except Exception:
                pass
            self._w = needed_w
            self._h = needed_h
            self._last_fit_w = needed_w
            self._last_fit_h = needed_h
        # Always center after size change
        self._center_embedded_widget_in_body(padding)
        # Relayout sockets if subclass implements
        layout_method = getattr(self, "_layout_sockets", None)
        if callable(layout_method):
            try:
                layout_method()  # type: ignore
            except Exception:
                pass

    def eventFilter(self, watched, event):  # NEW override
        if watched is self._embedded_widget and event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
            self._fit_node_to_widget()
        return super().eventFilter(watched, event)

    def _center_embedded_widget_in_body(self, padding: int = _CONTENT_PADDING):
        """Center the embedded widget in the content region (excluding title bar).

        Horizontal: centered within width minus padding.
        Vertical: centered within area below title bar. If the widget is taller
        than the content region, clamp to top (just below title bar) with padding.
        """
        if self._proxy is None:
            return
        widget = self._proxy.widget()
        if widget is None:
            return
        w = widget.width() or widget.sizeHint().width()
        h = widget.height() or widget.sizeHint().height()
        content_height = max(0.0, self._h - _TITLE_BAR_HEIGHT - padding)
        # Horizontal center inside padded area
        x = padding + max(0.0, (self._w - 2 * padding - w) / 2.0)
        # Vertical center inside content body (exclude title bar)
        if h >= content_height:
            y = _TITLE_BAR_HEIGHT + padding
        else:
            y = _TITLE_BAR_HEIGHT + (content_height - h) / 2.0
        self._proxy.setPos(x, y)

    def embedded_widget(self) -> QWidget | None:  # noqa: D401
        return self._embedded_widget

    # --- Socket accessors -------------------------------------------------
    def input_sockets(self) -> List[QD_NodeSocket]:  # camelCase
        return self._in_sockets if self._in_sockets is not None else []

    def output_sockets(self) -> List[QD_NodeSocket]:  # camelCase
        return self._out_sockets if self._out_sockets is not None else []

    def add_input_socket(self, socket: QD_NodeSocket | None = None, *, sock_type: SocketType | None = None) -> QD_NodeSocket:
        if self._in_sockets is None:
            self._in_sockets = []
        if socket is None:
            stype: SocketType = sock_type if sock_type is not None else self.default_socket_type(SocketDirection.IN)
            socket = QD_NodeSocket(SocketDirection.IN, self, stype)
        try:
            socket.setZValue(-0.5)
        except Exception:
            pass
        self._in_sockets.append(socket)
        return socket

    def add_output_socket(self, socket: QD_NodeSocket | None = None, *, sock_type: SocketType | None = None) -> QD_NodeSocket:
        if self._out_sockets is None:
            self._out_sockets = []
        if socket is None:
            stype: SocketType = sock_type if sock_type is not None else self.default_socket_type(SocketDirection.OUT)
            socket = QD_NodeSocket(SocketDirection.OUT, self, stype)
        try:
            socket.setZValue(-0.5)
        except Exception:
            pass
        self._out_sockets.append(socket)
        return socket

    def itemChange(self, change, value):  # Qt override keep camelCase
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

    # --- Resize helpers (NEW) -------------------------------------------
    def _detect_resize_edges(self, pos) -> tuple[bool, bool, bool, bool]:
        """Return (left, right, top, bottom) booleans if cursor is near edges.
        pos is in local coordinates.
        """
        m = _RESIZE_MARGIN
        within = 0 <= pos.x() <= self._w and 0 <= pos.y() <= self._h
        if not within:
            return False, False, False, False
        left = abs(pos.x() - 0) <= m
        right = abs(pos.x() - self._w) <= m
        top = abs(pos.y() - 0) <= m
        bottom = abs(pos.y() - self._h) <= m
        return left, right, top, bottom

    def _set_cursor_for_edges(self, left, right, top, bottom):  # NEW
        if self._resizing:
            return  # keep current cursor during active resize
        if (left or right) and (top or bottom):
            # Corner
            if (left and top) or (right and bottom):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif left or right:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif top or bottom:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _min_allowed_size(self):  # NEW
        pad = _CONTENT_PADDING
        if self._embedded_widget:
            w_needed = self._embedded_widget.sizeHint().width() + pad * 2
            h_needed = _TITLE_BAR_HEIGHT + self._embedded_widget.sizeHint().height() + pad
        else:
            w_needed = _MIN_NODE_WIDTH
            h_needed = _MIN_NODE_HEIGHT
        return max(_MIN_NODE_WIDTH, w_needed), max(_MIN_NODE_HEIGHT, h_needed)

    # --- Event overrides additions (NEW) --------------------------------
    def hoverMoveEvent(self, event):  # augment existing hover logic
        # existing hover logic preserved
        left, right, top, bottom = self._detect_resize_edges(event.pos())
        self._set_cursor_for_edges(left, right, top, bottom)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._resizing:
            left, right, top, bottom = self._detect_resize_edges(event.pos())
            if left or right or top or bottom:
                self._resizing = True
                self._resize_left = left
                self._resize_right = right
                self._resize_top = top
                self._resize_bottom = bottom
                self._resize_origin_scene = event.scenePos()
                self._orig_rect = (self.x(), self.y(), self._w, self._h)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._orig_rect is not None and self._resize_origin_scene is not None:
            ox, oy, ow, oh = self._orig_rect
            delta = event.scenePos() - self._resize_origin_scene
            dx = delta.x()
            dy = delta.y()
            new_x = ox
            new_y = oy
            new_w = ow
            new_h = oh
            if self._resize_left:
                new_w = ow - dx
                new_x = ox + dx
            if self._resize_right:
                new_w = ow + dx
            if self._resize_top:
                new_h = oh - dy
                new_y = oy + dy
            if self._resize_bottom:
                new_h = oh + dy
            # Enforce minimums and embedded widget constraints
            min_w, min_h = self._min_allowed_size()
            if new_w < min_w:
                # adjust x if dragging left
                if self._resize_left:
                    new_x -= (min_w - new_w)
                new_w = min_w
            if new_h < min_h:
                if self._resize_top:
                    new_y -= (min_h - new_h)
                new_h = min_h
            # Prevent negative width/height flips
            if new_w <= 0 or new_h <= 0:
                return
            # Apply geometry
            if (new_w != self._w) or (new_h != self._h):
                try:
                    self.prepareGeometryChange()
                except Exception:
                    pass
                self._w = new_w
                self._h = new_h
            if new_x != self.x() or new_y != self.y():
                # move triggers itemChange for edges
                self.setPos(new_x, new_y)
            # Recenter embedded widget & layout sockets
            try:
                self._center_embedded_widget_in_body()
            except Exception:
                pass
            layout_method = getattr(self, "_layout_sockets", None)
            if callable(layout_method):
                try:
                    layout_method()  # type: ignore
                except Exception:
                    pass
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing and event.button() == Qt.MouseButton.LeftButton:
            self._resizing = False
            self._resize_left = self._resize_right = self._resize_top = self._resize_bottom = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

__all__ = ["QD_Node"]
