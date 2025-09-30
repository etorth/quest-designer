# -*- coding: utf-8 -*-
"""Selector operation node.

A control-flow style node that selects between two outgoing PROCESS paths
based on a BOOL condition input (first IN socket). The second IN socket is a
PROCESS input (e.g., an upstream flow dependency). Two PROCESS OUT sockets
represent alternative outgoing branches / continuations.

Sockets:
  IN[0]: BOOL (condition)
  IN[1]: PROCESS (incoming control flow)
  OUT[0]: PROCESS (branch A)
  OUT[1]: PROCESS (branch B)

Currently this node is structural only (no evaluation logic). It mirrors the
conventions used by other op nodes (dynamic import shims + snake_case APIs).
"""
from importlib import import_module
from typing import Optional

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Selector"]


class Selector(QD_OpNode):
    def __init__(self, title: str = "Selector", parent: Optional[object] = None):
        # Initialize base with explicit empty socket arrays so we manually create sockets
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Inputs: BOOL (condition), PROCESS (incoming flow)
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.BOOL),
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS),
        ]
        # Outputs: two PROCESS branches
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS),
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS),
        ]
        # Layout sockets
        self._layout_sockets()

    def _layout_sockets(self):
        """Position input sockets on left and outputs on right."""
        w, h = self.size()
        # Ensure enough height for four sockets spacing if needed
        min_height = 80
        if h < min_height:
            self._h = min_height  # safe direct adjust (node not yet in scene typical)
            w, h = self.size()
        # Inputs vertically distributed
        if self._in_sockets:
            gap_in = h / (len(self._in_sockets) + 1)
            for idx, sock in enumerate(self._in_sockets, start=1):
                sock.setPos(-QD_NodeSocket.RADIUS, gap_in * idx)
        # Outputs vertically distributed (independent list)
        if self._out_sockets:
            gap_out = h / (len(self._out_sockets) + 1)
            for idx, sock in enumerate(self._out_sockets, start=1):
                sock.setPos(w + QD_NodeSocket.RADIUS, gap_out * idx)

    # Optional convenience accessors
    def condition_socket(self) -> QD_NodeSocket:
        return self._in_sockets[0]

    def flow_in_socket(self) -> QD_NodeSocket:
        return self._in_sockets[1]

    def branch_a_socket(self) -> QD_NodeSocket:
        return self._out_sockets[0]

    def branch_b_socket(self) -> QD_NodeSocket:
        return self._out_sockets[1]

