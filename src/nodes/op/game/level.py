# -*- coding: utf-8 -*-
"""Level operation node.

Represents a game level operation placeholder with a single input and output
socket (e.g., sequencing levels or gating flow). Future extensions could add
properties such as difficulty, environment, or prerequisites.
"""
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from nodes.qdopnode import QD_OpNode

__all__ = ["Level"]


class Level(QD_OpNode):
    def __init__(self, title: str = "Level", parent=None):
        # Initialize with explicit empty socket lists so base validation passes
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # One input, one output
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self)]
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self)]
        self._layout_sockets()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        # Input on left middle, output on right middle
        if self._in_sockets:
            self._in_sockets[0].setPos(0, h / 2)
        if self._out_sockets:
            self._out_sockets[0].setPos(w, h / 2)

