# -*- coding: utf-8 -*-
"""String concatenation operation node (Concat).

Concat node:
  IN[0]: STRING
  IN[1]: STRING
  OUT[0]: STRING (result of concatenation)

Purely structural at this stage (no runtime evaluation wired yet).
"""
from importlib import import_module


_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Concat"]


class Concat(QD_OpNode):
    """Concatenate two STRING inputs into one STRING output."""

    def __init__(self, title: str = "拼接", parent: object | None = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.STRING),
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.STRING),
        ]
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.STRING),
        ]
        self._layout_sockets()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_height = 70
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        gap_in = h / (len(self._in_sockets) + 1)
        for idx, sock in enumerate(self._in_sockets, start=1):
            sock.setPos(-QD_NodeSocket.RADIUS, gap_in * idx)
        out_sock = self._out_sockets[0]
        out_sock.setPos(w + QD_NodeSocket.RADIUS, h / 2)

    def left_socket(self) -> QD_NodeSocket:  # Convenience
        return self._in_sockets[0]

    def right_socket(self) -> QD_NodeSocket:  # Convenience
        return self._in_sockets[1]

    def result_socket(self) -> QD_NodeSocket:  # Convenience
        return self._out_sockets[0]

