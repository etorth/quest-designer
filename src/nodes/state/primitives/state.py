# -*- coding: utf-8 -*-
"""Primitive 'State' node.

Represents a basic state in the quest graph. It has:
- 1 input socket (PROCESS type) by default
- 1 output socket (PROCESS type) by default

Inherits from QD_StateNode (state-layer semantic base).
"""

from ...qdstatenode import QD_StateNode
from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType

__all__ = ["State"]


class State(QD_StateNode):
    def __init__(self, title: str = "State", parent=None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Create 1 IN and 1 OUT socket, both PROCESS type
        in_socket = QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS)
        out_socket = QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS)
        self._in_sockets = [in_socket]
        self._out_sockets = [out_socket]
        self._layout_sockets()

    def _layout_sockets(self):
        w, h = self.size()
        # Position IN socket on left edge, centered vertically
        if self._in_sockets:
            self._in_sockets[0].setPos(-QD_NodeSocket.RADIUS, h / 2.0)
        # Position OUT socket on right edge, centered vertically
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2.0)
