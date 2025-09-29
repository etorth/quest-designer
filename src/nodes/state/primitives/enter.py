# -*- coding: utf-8 -*-
"""Primitive 'Enter' node.

Represents a starting point (source) in the quest graph. It has:
- No input sockets
- Exactly one output socket

Inherits from QD_StateNode (state-layer semantic base).
"""

from ...qdstatenode import QD_StateNode  # changed base import
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore

__all__ = ["Enter"]


class Enter(QD_StateNode):  # changed base class
    def __init__(self, title: str = "Enter", parent=None):
        super().__init__(title=title, parent=parent, in_sockets=[])  # out_sockets created below
        out_socket = QD_NodeSocket(SocketDirection.OUT, parent=self)
        self._out_sockets = [out_socket]
        self._layout_sockets()

    def _layout_sockets(self):
        if self._out_sockets:
            sock = self._out_sockets[0]
            w, h = self.size()
            sock.setPos(w, h / 2.0)
