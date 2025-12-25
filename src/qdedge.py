# -*- coding: utf-8 -*-
"""Edge graphics item for QuestDesigner.

Semantics (UPDATED AGAIN):
- Creation requires at least one socket (OUT or IN). If both None -> error.
- An edge may be half-connected (one socket + temporary mouse endpoint) or completed (two sockets).
- If two sockets are connected they MUST have opposite directions (IN vs OUT); a second socket with same direction is rejected.
- The *beginning* point of the edge is the OUT socket (if present).
- The *ending* point of the edge is the IN socket (if present).
- Half-edge rules:
    * Only OUT socket: beginning=OUT socket, ending=mouse temp position.
    * Only IN socket: beginning=mouse temp position, ending=IN socket.
"""
from enum import Enum, auto

from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPainterPath, QPen, QColor
from PySide6.QtCore import QPointF, Qt

from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType

__all__ = ["QD_Edge", "EdgeStatus"]


class EdgeStatus(Enum):
    CONNECTING = auto()
    DONE = auto()
    DELETING = auto()


_EDGE_COLOR_NORMAL = QColor("#b8b8b8")
_EDGE_COLOR_CONNECTING = QColor("#9aa0a6")
_EDGE_COLOR_DELETING = QColor("#ff4d4d")
_EDGE_COLOR_SELECTED = QColor("#4da3ff")
_EDGE_COLOR_PROCESS = QColor("#d4af37")
_EDGE_COLOR_PROCESS_CONNECTING = QColor("#c39b2c")
_EDGE_COLOR_PROCESS_SELECTED = QColor("#ffdb5e")
_EDGE_COLOR_PROCESS_DELETING = QColor("#ff9f3d")


class QD_Edge(QGraphicsPathItem):
    def __init__(self, begin: QD_NodeSocket | None = None, end: QD_NodeSocket | None = None, parent: QGraphicsItem | None = None):
        super().__init__(parent)
        self._begin: QD_NodeSocket | None = None
        self._end: QD_NodeSocket | None = None
        self._status: EdgeStatus = EdgeStatus.CONNECTING
        self._temp_pos: QPointF | None = None
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(-1)
        if begin is None and end is None:
            raise ValueError("QD_Edge requires at least one initial socket (begin or end)")
        if begin:
            self.set_begin_socket(begin)
        if end:
            self.set_end_socket(end)
        self.update_path()

    # --- Socket management ------------------------------------------------
    def set_begin_socket(self, socket: QD_NodeSocket):
        if self._begin is socket:
            return
        if self._begin is not None:
            self._begin.remove_edge(self)
        self._begin = socket
        socket.add_edge(self)
        # _auto_orient removed (orientation handled logically elsewhere)
        self._update_status_after_socket_change()
        self.update_path()

    def set_end_socket(self, socket: QD_NodeSocket):
        if self._end is socket:
            return
        if self._end is not None:
            self._end.remove_edge(self)
        self._end = socket
        socket.add_edge(self)
        self._update_status_after_socket_change()
        self.update_path()

    def finalize_with(self, socket: QD_NodeSocket):
        if self._begin is None:
            self.set_begin_socket(socket)
        elif self._end is None:
            self.set_end_socket(socket)
        self._update_status_after_socket_change()

    def mark_deleting(self):
        self._status = EdgeStatus.DELETING
        self.update()

    def detach(self):
        if self._begin:
            self._begin.remove_edge(self)
        if self._end:
            self._end.remove_edge(self)
        self._begin = None
        self._end = None
        self._status = EdgeStatus.CONNECTING
        self._temp_pos = None
        self.update_path()

    # --- Status / orientation ---------------------------------------------
    def status(self) -> EdgeStatus:
        return self._status

    def _in_socket(self) -> QD_NodeSocket | None:
        if self._begin and self._begin.direction() == SocketDirection.IN:
            return self._begin
        if self._end and self._end.direction() == SocketDirection.IN:
            return self._end
        return None

    def _out_socket(self) -> QD_NodeSocket | None:
        if self._begin and self._begin.direction() == SocketDirection.OUT:
            return self._begin
        if self._end and self._end.direction() == SocketDirection.OUT:
            return self._end
        return None

    def _validate_direction_pair(self):
        """Reject invalid second socket if both share same direction."""
        if self._begin and self._end and self._begin.direction() == self._end.direction():
            # Reject the later-added (_end) socket
            try:
                self._end.remove_edge(self)
            except Exception:
                pass
            self._end = None
            self._status = EdgeStatus.CONNECTING

    def _update_status_after_socket_change(self):  # override with validation
        self._validate_direction_pair()
        if self._status == EdgeStatus.DELETING:
            return
        in_sock = self._in_socket()
        out_sock = self._out_socket()
        if in_sock and out_sock:
            self._status = EdgeStatus.DONE
            self._temp_pos = None
        else:
            self._status = EdgeStatus.CONNECTING

    def _is_process_edge(self) -> bool:
        """Return True if any connected socket is of PROCESS type.

        Safe against partially connected (CONNECTING) edges.
        """
        try:
            ins = self._in_socket()
            if ins and ins.socket_type() == SocketType.PROCESS:
                return True
            outs = self._out_socket()
            if outs and outs.socket_type() == SocketType.PROCESS:
                return True
        except Exception:
            pass
        return False

    # --- Dynamic connecting -----------------------------------------------
    def update_dynamic_end(self, scene_pos: QPointF):
        if self._status != EdgeStatus.CONNECTING:
            return
        if self._begin and self._end:
            return
        self._temp_pos = scene_pos
        self.update_path()

    # --- Geometry/path ----------------------------------------------------
    def _endpoint_positions(self) -> tuple[QPointF, QPointF] | None:
        """Return (p_begin, p_end) according to new semantics OUT->IN.

        p_begin = OUT socket or temp
        p_end   = IN  socket or temp
        """
        # Identify sockets
        out_sock = None
        in_sock = None
        if self._begin:
            if self._begin.direction() == SocketDirection.OUT:
                out_sock = self._begin
            else:
                in_sock = self._begin
        if self._end:
            if self._end.direction() == SocketDirection.OUT:
                out_sock = out_sock or self._end
            else:
                in_sock = in_sock or self._end
        # Completed edge
        if out_sock and in_sock:
            return out_sock.connection_point(), in_sock.connection_point()
        # Half edge during connecting
        if self._status == EdgeStatus.CONNECTING and self._temp_pos is not None:
            if out_sock and not in_sock:
                return out_sock.connection_point(), self._temp_pos
            if in_sock and not out_sock:
                return self._temp_pos, in_sock.connection_point()
        return None

    def update_path(self):
        endpoints = self._endpoint_positions()
        path = QPainterPath()
        if endpoints is None:
            self.setPath(path)
            self.update()
            return
        p_begin, p_end = endpoints
        path.moveTo(p_begin)
        if p_begin == p_end:
            path.addEllipse(p_begin, 1.5, 1.5)
        else:
            raw_dx = p_end.x() - p_begin.x()
            if raw_dx >= 0:
                base_mag = max(40.0, min(abs(raw_dx) * 0.5, 200.0))
            else:
                base_mag = max(40.0, min(abs(raw_dx) * 0.35, 120.0))
            ctrl1 = QPointF(p_begin.x() + base_mag, p_begin.y())
            ctrl2 = QPointF(p_end.x() - base_mag, p_end.y())
            if (p_end.x() - ctrl2.x()) < 10:
                mid_x = (p_begin.x() + p_end.x()) / 2.0
                ctrl2 = QPointF(mid_x, p_end.y())
            path.cubicTo(ctrl1, ctrl2, p_end)
        self.setPath(path)
        self.update()

    # --- Painting ---------------------------------------------------------
    def paint(self, painter, option, widget=None):  # Qt override
        is_process_edge = self._is_process_edge()
        if self._status == EdgeStatus.DELETING:
            color = _EDGE_COLOR_PROCESS_DELETING if is_process_edge else _EDGE_COLOR_DELETING
        elif self._status == EdgeStatus.CONNECTING:
            color = _EDGE_COLOR_PROCESS_CONNECTING if is_process_edge else _EDGE_COLOR_CONNECTING
        else:
            color = _EDGE_COLOR_PROCESS if is_process_edge else _EDGE_COLOR_NORMAL
        if self.isSelected() and self._status != EdgeStatus.DELETING:
            color = _EDGE_COLOR_PROCESS_SELECTED if is_process_edge else _EDGE_COLOR_SELECTED
        base_width = 3 if is_process_edge else 2
        pen = QPen(color, base_width)
        if self._status == EdgeStatus.CONNECTING:
            pen.setStyle(Qt.PenStyle.DashLine)
        if self._status == EdgeStatus.DELETING:
            pen.setWidth(base_width + 0)
            pen.setStyle(Qt.PenStyle.DashDotLine)
        if self.isSelected():
            pen.setWidth(pen.width() + 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())
        # Arrowhead intentionally removed per user request (no directional marker)

    # --- Utilities --------------------------------------------------------
    def begin_socket(self) -> QD_NodeSocket | None:
        return self._begin

    def end_socket(self) -> QD_NodeSocket | None:
        return self._end

    def is_complete(self) -> bool:
        return self._status == EdgeStatus.DONE and self._begin is not None and self._end is not None

    def is_connecting(self) -> bool:
        return self._status == EdgeStatus.CONNECTING

    def is_deleting(self) -> bool:
        return self._status == EdgeStatus.DELETING
