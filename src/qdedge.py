# -*- coding: utf-8 -*-
"""Edge graphics item for QuestDesigner.

Semantics (UPDATED):
- An edge may have 1 or 2 sockets connected.
- If two sockets are connected they must have opposite directions (IN vs OUT).
- The "beginning point" of the drawn curve is the IN socket (if present).
- The "ending point" of the drawn curve is the OUT socket (if present).
- For a half (CONNECTING) edge:
    * If only an IN socket is attached: curve starts at that IN socket and ends at the mouse (temp) position.
    * If only an OUT socket is attached: curve ends at that OUT socket and begins at the mouse (temp) position.
"""
from enum import Enum, auto
from typing import Optional, Tuple

from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPainterPath, QPen, QColor
from PySide6.QtCore import QPointF, Qt

from qdnodesocket import QD_NodeSocket, SocketDirection

__all__ = ["QD_Edge", "EdgeStatus"]


class EdgeStatus(Enum):
    CONNECTING = auto()
    DONE = auto()
    DELETING = auto()


_EDGE_COLOR_NORMAL = QColor("#b8b8b8")
_EDGE_COLOR_CONNECTING = QColor("#9aa0a6")
_EDGE_COLOR_DELETING = QColor("#ff4d4d")
_EDGE_COLOR_SELECTED = QColor("#4da3ff")


class QD_Edge(QGraphicsPathItem):
    def __init__(self, begin: Optional[QD_NodeSocket] = None, end: Optional[QD_NodeSocket] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self._begin: Optional[QD_NodeSocket] = None
        self._end: Optional[QD_NodeSocket] = None
        self._status: EdgeStatus = EdgeStatus.CONNECTING
        self._temp_pos: Optional[QPointF] = None
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(-1)
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

    def _in_socket(self) -> Optional[QD_NodeSocket]:
        if self._begin and self._begin.direction() == SocketDirection.IN:
            return self._begin
        if self._end and self._end.direction() == SocketDirection.IN:
            return self._end
        return None

    def _out_socket(self) -> Optional[QD_NodeSocket]:
        if self._begin and self._begin.direction() == SocketDirection.OUT:
            return self._begin
        if self._end and self._end.direction() == SocketDirection.OUT:
            return self._end
        return None

    def _validate_direction_pair(self):
        """Ensure if two sockets are present they have opposite directions.
        If they don't, drop the later-attached (stored in _end) to preserve edge validity.
        """
        if self._begin and self._end:
            if self._begin.direction() == self._end.direction():
                # Remove the second one silently (could alternatively mark DELETING)
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

    # --- Dynamic connecting -----------------------------------------------
    def update_dynamic_end(self, scene_pos: QPointF):
        if self._status != EdgeStatus.CONNECTING:
            return
        if self._begin and self._end:
            return
        self._temp_pos = scene_pos
        self.update_path()

    # --- Geometry/path ----------------------------------------------------
    def _endpoint_positions(self) -> Optional[Tuple[QPointF, QPointF]]:
        in_sock = self._in_socket()
        out_sock = self._out_socket()
        # Both sockets present: p1 is IN, p2 is OUT
        if in_sock and out_sock:
            return in_sock.connection_point(), out_sock.connection_point()
        # Half edge logic
        if self._status == EdgeStatus.CONNECTING and self._temp_pos is not None:
            if in_sock and not out_sock:
                # start at IN, end at temp
                return in_sock.connection_point(), self._temp_pos
            if out_sock and not in_sock:
                # start at temp, end at OUT
                return self._temp_pos, out_sock.connection_point()
        # No endpoints or insufficient info
        return None

    def update_path(self):
        endpoints = self._endpoint_positions()
        path = QPainterPath()
        if endpoints is None:
            self.setPath(path)
            self.update()
            return
        p1, p2 = endpoints
        path.moveTo(p1)
        if p1 == p2:
            path.addEllipse(p1, 1.5, 1.5)
        else:
            raw_dx = p2.x() - p1.x()
            # Adaptive curvature: different clamp when edge flows leftwards
            if raw_dx >= 0:
                base_mag = max(40.0, min(abs(raw_dx) * 0.5, 200.0))
            else:
                base_mag = max(40.0, min(abs(raw_dx) * 0.35, 120.0))
            ctrl1 = QPointF(p1.x() + base_mag, p1.y())
            ctrl2 = QPointF(p2.x() - base_mag, p2.y())
            if (p2.x() - ctrl2.x()) < 10:  # tighten second control
                mid_x = (p1.x() + p2.x()) / 2.0
                ctrl2 = QPointF(mid_x, p2.y())
            path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)
        self.update()

    # --- Painting ---------------------------------------------------------
    def paint(self, painter, option, widget=None):  # Qt override
        if self._status == EdgeStatus.DELETING:
            color = _EDGE_COLOR_DELETING
        elif self._status == EdgeStatus.CONNECTING:
            color = _EDGE_COLOR_CONNECTING
        else:
            color = _EDGE_COLOR_NORMAL
        if self.isSelected() and self._status != EdgeStatus.DELETING:
            color = _EDGE_COLOR_SELECTED
        pen = QPen(color, 2)
        if self._status == EdgeStatus.CONNECTING:
            pen.setStyle(Qt.PenStyle.DashLine)
        if self._status == EdgeStatus.DELETING:
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashDotLine)
        if self.isSelected():
            pen.setWidth(pen.width() + 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())
        # Arrowhead at ending point (OUT socket end) if complete
        try:
            in_sock = self._in_socket()
            out_sock = self._out_socket()
            if out_sock and (in_sock or self._status == EdgeStatus.CONNECTING):
                # Determine end point and tangent
                p_end = out_sock.connection_point() if in_sock and out_sock else None
                if p_end is None and self._status == EdgeStatus.CONNECTING and out_sock:
                    p_end = out_sock.connection_point()
                if p_end is not None:
                    # Approximate tangent using last segment
                    length_approx_p = self.path().pointAtPercent(1.0)
                    back_approx = self.path().pointAtPercent(0.985)
                    vx = length_approx_p.x() - back_approx.x()
                    vy = length_approx_p.y() - back_approx.y()
                    mag = (vx * vx + vy * vy) ** 0.5 or 1.0
                    ux, uy = vx / mag, vy / mag
                    arrow_len = 10.0
                    wing = 5.0
                    tip = length_approx_p
                    left = QPointF(tip.x() - ux * arrow_len + (-uy) * wing,
                                   tip.y() - uy * arrow_len + ux * wing)
                    right = QPointF(tip.x() - ux * arrow_len + uy * wing,
                                    tip.y() - uy * arrow_len - ux * wing)
                    painter.setBrush(color)
                    painter.drawPolygon(tip, left, right)
        except Exception:
            pass

    # --- Utilities --------------------------------------------------------
    def begin_socket(self) -> Optional[QD_NodeSocket]:
        return self._begin

    def end_socket(self) -> Optional[QD_NodeSocket]:
        return self._end

    def is_complete(self) -> bool:
        return self._status == EdgeStatus.DONE and self._begin is not None and self._end is not None

    def is_connecting(self) -> bool:
        return self._status == EdgeStatus.CONNECTING

    def is_deleting(self) -> bool:
        return self._status == EdgeStatus.DELETING

