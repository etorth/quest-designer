# -*- coding: utf-8 -*-
"""Primitive 'Enter' node.

Represents a starting point (source) in the quest graph. It has:
- No input sockets
- Exactly one output socket

Future behavior can include automatically spawning default flow edges, or
special rendering/styles for root nodes.
"""
from __future__ import annotations

from qdnode import QD_Node  # type: ignore
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore

__all__ = ["Enter"]


class Enter(QD_Node):
    def __init__(self, title: str = "Enter", parent=None):
        # No in_sockets, will supply an empty list explicitly for clarity.
        super().__init__(title=title, parent=parent, in_sockets=[])  # out_sockets created below
        # Create a single OUT socket
        out_socket = QD_NodeSocket(SocketDirection.OUT, parent=self)
        self._out_sockets = [out_socket]
        # Optionally position the socket at middle-right edge (simple heuristic)
        self._layout_sockets()

    # Simple internal layout helper (not part of base API yet)
    def _layout_sockets(self):
        if self._out_sockets:
            sock = self._out_sockets[0]
            w, h = self.size()
            # Place center exactly on node's right edge so half-circle chord is flush
            sock.setPos(w, h / 2.0)
