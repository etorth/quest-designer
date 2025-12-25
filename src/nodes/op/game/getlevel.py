# -*- coding: utf-8 -*-
"""GetLevel operation node.

Produces the (integer) current level value as an INTEGER typed output.
This node acts as a source: no input sockets, exactly one INTEGER OUT socket.

Sockets:
  OUT[0]: INTEGER (level value)
"""
from importlib import import_module


_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["GetLevel"]


class GetLevel(QD_OpNode):
    def __init__(self, title: str = "等级值", parent: object | None = None):
        # Explicit empty socket lists; we add only an OUT INTEGER socket
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.INTEGER)
        ]
        self._layout_sockets()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        # Modest minimum height to center the socket nicely
        min_height = 60
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)

    def out_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._out_sockets[0]

