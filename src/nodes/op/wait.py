# -*- coding: utf-8 -*-
"""Wait operation node.

A control-flow style node similar to ``Selector`` but with only one outgoing
PROCESS path.

Sockets:
  IN[0]: BOOL (condition)
  IN[1]: PROCESS (incoming flow / dependency)
  OUT[0]: PROCESS (continuation)
"""
from importlib import import_module


_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Wait"]


class Wait(QD_OpNode):
    def __init__(self, title: str = "等待", parent: object | None = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.BOOL),
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS),
        ]
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS),
        ]
        self._layout_sockets()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_height = 80
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        if self._in_sockets:
            gap_in = h / (len(self._in_sockets) + 1)
            for idx, sock in enumerate(self._in_sockets, start=1):
                sock.setPos(-QD_NodeSocket.RADIUS, gap_in * idx)
        if self._out_sockets:
            gap_out = h / (len(self._out_sockets) + 1)
            for idx, sock in enumerate(self._out_sockets, start=1):
                sock.setPos(w + QD_NodeSocket.RADIUS, gap_out * idx)

    def condition_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._in_sockets[0]

    def flow_in_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._in_sockets[1]

    def continuation_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._out_sockets[0]

