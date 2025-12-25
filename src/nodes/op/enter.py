# -*- coding: utf-8 -*-
"""Enter operation node.

A start/control entry point node analogous in layout to ``Selector`` but with
no incoming sockets. It now provides a single PROCESS output socket.
Displays as a circular shape.

Sockets:
  OUT[0]: PROCESS (continuation)
"""
from importlib import import_module
from PySide6.QtGui import QPainter, QPen, QBrush, QFont
from PySide6.QtCore import QRectF, Qt


_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Enter"]


class Enter(QD_OpNode):
    def __init__(self, title: str = "入口", parent: object | None = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Make it square so circle fits properly
        self._w = 80
        self._h = 80
        # Single PROCESS outgoing continuation
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS),
        ]
        self._layout_sockets()

    def boundingRect(self) -> QRectF:  # Qt override
        # Circular bounding box
        return QRectF(0, 0, self._w, self._h).adjusted(-1, -1, 1, 1)

    def paint(self, painter: QPainter, option, widget=None):  # Qt override
        # Import colors from parent module
        try:
            from qdnode import _NODE_BASE_COLOR, _NODE_BASE_SELECTED, _NODE_BORDER_COLOR, _NODE_BORDER_HOVER, _NODE_BORDER_SELECTED, _NODE_TEXT_COLOR
        except ImportError:
            # Fallback colors
            from PySide6.QtGui import QColor
            _NODE_BASE_COLOR = QColor("#272b30")
            _NODE_BASE_SELECTED = QColor("#2b6fe6")
            _NODE_BORDER_COLOR = QColor("#222")
            _NODE_BORDER_HOVER = QColor("#444")
            _NODE_BORDER_SELECTED = QColor("#5c9dff")
            _NODE_TEXT_COLOR = QColor("#ffffff")

        # Base colors
        base_color = _NODE_BASE_COLOR
        if self._hover and not self.isSelected():
            base_color = base_color.lighter(120)
        if self.isSelected():
            base_color = _NODE_BASE_SELECTED
        
        # Border color & thickness
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
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(base_color))
        
        # Draw circle (ellipse with equal width and height)
        painter.drawEllipse(QRectF(0, 0, self._w, self._h))
        
        # Title text centered
        painter.setPen(_NODE_TEXT_COLOR)
        font: QFont = painter.font()
        font.setBold(True)
        font.setPointSizeF(max(font.pointSizeF() * 0.9, 8))
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, self._w, self._h),
                         Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, self._title)

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        if self._out_sockets:
            # Single socket placed vertically centered
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)

    def out_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._out_sockets[0]

