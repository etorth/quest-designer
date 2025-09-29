# -*- coding: utf-8 -*-
"""Primitive 'Exit' node.

Represents an ending point (drain) in the quest graph. It has:
- Exactly one input socket
- No output sockets

Future behavior can include validation ensuring at least one incoming edge,
or special visual styling to distinguish terminal nodes.
"""
from __future__ import annotations

from qdnode import QD_Node  # type: ignore
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore

__all__ = ["Exit"]


class Exit(QD_Node):
    def __init__(self, title: str = "Exit", parent=None):
        # Provide explicit empty out_sockets list; will add 1 IN socket after init.
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Create a single IN socket
        in_socket = QD_NodeSocket(SocketDirection.IN, parent=self)
        self._in_sockets = [in_socket]
        self._layout_sockets()

    def _layout_sockets(self):
        if self._in_sockets:
            sock = self._in_sockets[0]
            w, h = self.size()
            # Place center exactly on node's left edge so half-circle chord is flush
            sock.setPos(0, h / 2.0)
