# -*- coding: utf-8 -*-
"""Exit operation node.

A control/exit node analogous in layout to ``Enter`` but with a single incoming PROCESS socket and no outgoing sockets.

Sockets:
  IN[0]: PROCESS (continuation)
"""
from importlib import import_module


_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Exit"]


class Exit(QD_OpNode):
    def __init__(self, title: str = "出口", parent: object | None = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Single PROCESS incoming continuation
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS),
        ]
        self._layout_sockets()

    def _layout_sockets(self):
        w, h = self.size()
        min_height = 60
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        if self._in_sockets:
            # Single socket placed vertically centered
            self._in_sockets[0].setPos(-QD_NodeSocket.RADIUS, h / 2)

    def in_socket(self) -> QD_NodeSocket:
        return self._in_sockets[0]

