# -*- coding: utf-8 -*-
"""Primitive 'Exit' node.

Represents an ending point (drain) in the quest graph. It has:
- Exactly one input socket
- No output sockets

Inherits from QD_StateNode (state-layer semantic base).
"""

from ...qdstatenode import QD_StateNode  # changed base import
from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType  # UPDATED import

__all__ = ["Exit"]


class Exit(QD_StateNode):  # changed base class
    def __init__(self, title: str = "Exit", parent=None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        in_socket = QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.BOOL)
        self._in_sockets = [in_socket]
        self._layout_sockets()

    def _layout_sockets(self):
        if self._in_sockets:
            sock = self._in_sockets[0]
            w, h = self.size()
            sock.setPos(-QD_NodeSocket.RADIUS, h / 2.0)
