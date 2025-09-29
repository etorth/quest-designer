# -*- coding: utf-8 -*-
"""HasItem operation node.

Represents a condition check or operation that determines whether the player
(or another entity) possesses a particular item. For now this is a structural
placeholder node with one input and one output socket. Future enhancements
could add an embedded UI (e.g., item selector combo, quantity spin box).
"""
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from nodes.qdopnode import QD_OpNode

__all__ = ["HasItem"]


class HasItem(QD_OpNode):
    def __init__(self, title: str = "HasItem", parent=None):
        # Initialize base with explicit empty socket lists so we can construct manually
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # One input (flow comes in) and one output (flow continues if condition passes)
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self)]
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self)]
        self._layout_sockets()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        if self._in_sockets:
            self._in_sockets[0].setPos(0, h / 2)
        if self._out_sockets:
            self._out_sockets[0].setPos(w, h / 2)

