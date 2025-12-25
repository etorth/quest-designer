# -*- coding: utf-8 -*-
"""GetItem operation node.

Produces the (integer) count of a selected item. Acts as a source node:
- No IN sockets
- One INTEGER OUT socket

Embedded widget: a QComboBox listing classic Legend of Mir style items.
"""
from importlib import import_module

from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["GetItem"]


class GetItem(QD_OpNode):
    def __init__(self, title: str = "物品数量", parent: object | None = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Single INTEGER output
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.INTEGER)
        ]
        self._init_embedded_ui()
        self._layout_sockets()

    def _init_embedded_ui(self):  # noqa: D401
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._combo_item = QComboBox(container)
        self._items = ["金币", "木剑", "太阳水"]
        self._combo_item.addItems(self._items)
        self._combo_item.setMinimumContentsLength(2)
        layout.addWidget(self._combo_item)
        self.set_embedded_widget(container, auto_resize=True)

    def item_name(self) -> str:  # noqa: D401
        return self._combo_item.currentText()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_h = 60
        if h < min_h:
            self._h = min_h
            w, h = self.size()
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)

