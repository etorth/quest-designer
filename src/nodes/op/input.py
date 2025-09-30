# -*- coding: utf-8 -*-
"""Input operation node.

A simple source node that produces a STRING value. Currently minimal:
- No IN sockets
- One OUT socket of STRING type

Can be extended later with an embedded QLineEdit or constant picker.
"""
from importlib import import_module
from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLineEdit  # NEW imports

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Input"]


class Input(QD_OpNode):
    def __init__(self, title: str = "输入", parent: Optional[object] = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Single STRING output socket
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.STRING)
        ]
        self._init_embedded_ui()  # NEW: create embedded UI before layout
        self._layout_sockets()

    def _init_embedded_ui(self):  # noqa: D401 NEW
        """Build embedded widget: horizontal layout with combo + line edit."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._combo_type = QComboBox(container)
        # Keep list minimal (could later drive socket type); currently informational.
        self._combo_type.addItems(["STRING"])  # Single option for now
        self._line_value = QLineEdit(container)
        self._line_value.setPlaceholderText("输入文本...")
        layout.addWidget(self._combo_type)
        layout.addWidget(self._line_value, 1)
        self.set_embedded_widget(container, auto_resize=True)

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_h = 60
        if h < min_h:
            self._h = min_h
            w, h = self.size()
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)

    def out_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._out_sockets[0]
