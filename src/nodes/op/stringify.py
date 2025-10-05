# -*- coding: utf-8 -*-
"""Stringify operation node.

Converts an incoming INTEGER value to a STRING representation.
Structure only (no evaluation runtime implemented yet).

Sockets:
  IN[0]: INTEGER
  OUT[0]: STRING
"""
from importlib import import_module
from typing import Optional

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Stringify"]


class Stringify(QD_OpNode):
    def __init__(self, title: str = "字符串化", parent: Optional[object] = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # One INTEGER input
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.INTEGER),
        ]
        # One STRING output
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.STRING),
        ]
        self._layout_sockets()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_height = 60
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        # Input on left vertically centered
        in_sock = self._in_sockets[0]
        in_sock.setPos(-QD_NodeSocket.RADIUS, h / 2)
        # Output on right vertically centered
        out_sock = self._out_sockets[0]
        out_sock.setPos(w + QD_NodeSocket.RADIUS, h / 2)

    def input_socket(self) -> QD_NodeSocket:
        return self._in_sockets[0]

    def output_socket(self) -> QD_NodeSocket:
        return self._out_sockets[0]

