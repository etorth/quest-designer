# -*- coding: utf-8 -*-
"""Edge graphics item for QuestDesigner.

Refactored: project-local APIs now snake_case (Qt event names preserved).
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
        self._auto_orient()
        self._update_status_after_socket_change()
        self.update_path()

    def set_end_socket(self, socket: QD_NodeSocket):
        if self._end is socket:
            return
        if self._end is not None:
            self._end.remove_edge(self)
        self._end = socket
        socket.add_edge(self)
        self._auto_orient()
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

    def _update_status_after_socket_change(self):
        if self._status == EdgeStatus.DELETING:
            return
        if self._begin and self._end:
            self._status = EdgeStatus.DONE
            self._temp_pos = None
        else:
            self._status = EdgeStatus.CONNECTING

    def _auto_orient(self):
        if self._begin and self._end:
            if (self._begin.direction() == SocketDirection.IN and
                    self._end.direction() == SocketDirection.OUT):
                self._begin, self._end = self._end, self._begin

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
        if self._begin and self._end:
            return self._begin.connection_point(), self._end.connection_point()
        if self._status == EdgeStatus.CONNECTING and self._temp_pos is not None:
            if self._begin and not self._end:
                return self._begin.connection_point(), self._temp_pos
            if self._end and not self._begin:
                return self._temp_pos, self._end.connection_point()
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
            # Horizontal offset ensures first control point is to the RIGHT of start
            raw_dx = p2.x() - p1.x()
            # Base magnitude: half of horizontal distance or a minimum value
            base_mag = max(40.0, abs(raw_dx) * 0.5)
            # First control point: always to the right of p1 (even if edge goes left)
            ctrl1 = QPointF(p1.x() + base_mag, p1.y())
            # Second control point: mirror-style toward p2 (keeps curve smooth)
            ctrl2 = QPointF(p2.x() - base_mag, p2.y())
            # If p2.x() is very close to p1.x(), ctrl2 might cross p1; clamp to midpoint to avoid extreme fold
            if (p2.x() - ctrl2.x()) < 10:  # too tight, relax
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
