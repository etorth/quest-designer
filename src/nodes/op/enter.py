# -*- coding: utf-8 -*-
"""Enter operation node.

A start/control entry point node analogous in layout to ``Selector`` but with
no incoming sockets. It now provides a single PROCESS output socket.

Sockets:
  OUT[0]: PROCESS (continuation)
"""
from importlib import import_module
from typing import Optional

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Enter"]


class Enter(QD_OpNode):
    def __init__(self, title: str = "入口", parent: Optional[object] = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Single PROCESS outgoing continuation
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS),
        ]
        self._layout_sockets()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_height = 60
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        if self._out_sockets:
            # Single socket placed vertically centered
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)

    def out_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._out_sockets[0]
