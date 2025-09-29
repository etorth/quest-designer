# -*- coding: utf-8 -*-
"""Edge graphics item for QuestDesigner.

QD_Edge connects two QD_NodeSocket instances (begin -> end). It supports a
lifecycle with multiple statuses:

Statuses:
- CONNECTING: A provisional edge while user is dragging from one socket toward
  another. Only one socket is bound; the other endpoint follows a temporary
  position (updated via update_dynamic_end()).
- DONE: Both sockets are connected; edge is finalized.
- DELETING: Edge is flagged for removal and drawn with a distinct style.

Core behaviors:
- Smooth cubic Bézier path between endpoints (pleasant visual over straight line)
- Automatic orientation (first assigned socket becomes 'begin'). If later the
  second socket has OUT direction and first was IN, they are swapped to ensure
  logical OUT -> IN visual ordering (non-destructive orientation pass).
- Visual feedback for selection & different status colors.

Future extensions (not yet implemented):
- Edge labels / execution types
- Hit shape refinement for easier selection
- Dynamic updates when sockets move (currently requires manual update_path call)
- Validation (prevent multiple connections if socket disallows it)
- Hover effects & context menu
"""
from __future__ import annotations

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


# Palette / style map
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
        self.setZValue(-1)  # draw beneath nodes/sockets

        if begin:
            self.set_begin_socket(begin)
        if end:
            self.set_end_socket(end)
        self.update_path()

    # --- Socket management ------------------------------------------------
    def set_begin_socket(self, socket: QD_NodeSocket):
        self._begin = socket
        self._auto_orient()
        self._update_status_after_socket_change()
        self.update_path()

    def set_end_socket(self, socket: QD_NodeSocket):
        self._end = socket
        self._auto_orient()
        self._update_status_after_socket_change()
        self.update_path()

    def finalize_with(self, socket: QD_NodeSocket):  # convenience
        if self._begin is None:
            self.set_begin_socket(socket)
        elif self._end is None:
            self.set_end_socket(socket)
        self._update_status_after_socket_change()

    def mark_deleting(self):
        self._status = EdgeStatus.DELETING
        self.update()

    # --- Status / orientation ---------------------------------------------
    def status(self) -> EdgeStatus:
        return self._status

    def _update_status_after_socket_change(self):
        if self._status == EdgeStatus.DELETING:
            return  # keep deleting status sticky
        if self._begin and self._end:
            self._status = EdgeStatus.DONE
            self._temp_pos = None
        else:
            self._status = EdgeStatus.CONNECTING

    def _auto_orient(self):
        """Ensure OUT -> IN ordering when both sockets present.
        (Purely cosmetic orientation; does not modify actual graph semantics.)"""
        if self._begin and self._end:
            if (self._begin.direction() == SocketDirection.IN and
                    self._end.direction() == SocketDirection.OUT):
                # Swap so path flows left->right or out->in visually
                self._begin, self._end = self._end, self._begin

    # --- Dynamic connecting -----------------------------------------------
    def update_dynamic_end(self, scene_pos: QPointF):
        """While in CONNECTING status with only one socket, set the temporary
        floating endpoint (mouse-driven)."""
        if self._status != EdgeStatus.CONNECTING:
            return
        if self._begin and self._end:
            return  # already complete
        self._temp_pos = scene_pos
        self.update_path()

    # --- Geometry/path ----------------------------------------------------
    def _endpoint_positions(self) -> Optional[Tuple[QPointF, QPointF]]:
        if self._begin and self._end:
            p1 = self._begin.scenePos()
            p2 = self._end.scenePos()
            return p1, p2
        # CONNECTING with one socket and temp pos
        if self._status == EdgeStatus.CONNECTING and self._temp_pos is not None:
            if self._begin and not self._end:
                return self._begin.scenePos(), self._temp_pos
            if self._end and not self._begin:
                return self._temp_pos, self._end.scenePos()
        return None

    def update_path(self):  # public so external controllers can force recompute
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
            # Cubic curve with horizontal-ish tangents
            dx = (p2.x() - p1.x()) * 0.5
            ctrl1 = QPointF(p1.x() + dx, p1.y())
            ctrl2 = QPointF(p2.x() - dx, p2.y())
            # If nearly vertical, adjust to vertical curve
            if abs(p2.x() - p1.x()) < 10:
                dy = (p2.y() - p1.y()) * 0.5
                ctrl1 = QPointF(p1.x(), p1.y() + dy)
                ctrl2 = QPointF(p2.x(), p2.y() - dy)
            path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)
        self.update()

    # --- Painting ---------------------------------------------------------
    def paint(self, painter, option, widget=None):  # noqa: D401
        # Choose base color
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
        pen.setCosmetic(True)  # keeps width constant during zoom
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

    # --- Utilities --------------------------------------------------------
    def begin_socket(self) -> Optional[QD_NodeSocket]:  # noqa: D401
        return self._begin

    def end_socket(self) -> Optional[QD_NodeSocket]:  # noqa: D401
        return self._end

    def is_complete(self) -> bool:  # noqa: D401
        return self._status == EdgeStatus.DONE and self._begin is not None and self._end is not None

    def is_connecting(self) -> bool:  # noqa: D401
        return self._status == EdgeStatus.CONNECTING

    def is_deleting(self) -> bool:  # noqa: D401
        return self._status == EdgeStatus.DELETING

