# -*- coding: utf-8 -*-
"""NPCChat operation node.

Represents an NPC dialog trigger / line in a quest flow.

Sockets:
  IN[0]: STRING   (dialog text or speaker id upstream)
  IN[1]: PROCESS  (incoming execution flow)
  OUT[0]: PROCESS (continuation after chat finishes)

Currently structural only (no execution engine attached). The STRING input is
kept generic so upstream nodes can supply either localized text, a key, or an
NPC identifier resolved later.
"""
from importlib import import_module
from typing import Optional

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["NPCChat"]


class NPCChat(QD_OpNode):
    def __init__(self, title: str = "NPC对话", parent: Optional[object] = None):
        # Explicit no automatic sockets from base
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Inputs: STRING content / id, PROCESS control flow
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.STRING),
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS),
        ]
        # Output: PROCESS continuation
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS),
        ]
        self._layout_sockets()

    # Socket layout similar to Selector (2 ins, 1 out)
    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_height = 80
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        if self._in_sockets:
            gap_in = h / (len(self._in_sockets) + 1)
            for idx, sock in enumerate(self._in_sockets, start=1):
                sock.setPos(-QD_NodeSocket.RADIUS, gap_in * idx)
        if self._out_sockets:
            gap_out = h / (len(self._out_sockets) + 1)
            for idx, sock in enumerate(self._out_sockets, start=1):
                sock.setPos(w + QD_NodeSocket.RADIUS, gap_out * idx)

    # Convenience accessors
    def text_in_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._in_sockets[0]

    def flow_in_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._in_sockets[1]

    def flow_out_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._out_sockets[0]

