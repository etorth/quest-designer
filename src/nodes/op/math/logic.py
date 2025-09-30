# -*- coding: utf-8 -*-
"""Logic operation node (refactored to snake_case project APIs)."""
from importlib import import_module
from PySide6.QtWidgets import QComboBox

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Logic"]


class Logic(QD_OpNode):
    MIN_INPUTS = 2

    def __init__(self, title: str = "逻辑运算", parent=None, in_count: int = 2):
        if in_count < self.MIN_INPUTS:
            in_count = self.MIN_INPUTS
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Inputs
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.BOOL) for _ in range(in_count)]
        # Output
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.BOOL)]
        # Embedded logical operation selector combo
        self._op_combo = QComboBox()
        self._operations = ["与", "或", "非"]
        self._op_combo.addItems(self._operations)
        self._current_op = self._op_combo.currentText()
        self._op_combo.currentTextChanged.connect(self._on_op_changed)
        self.set_embedded_widget(self._op_combo, auto_resize=True)
        self._layout_sockets()

    def _on_op_changed(self, text: str):  # noqa: D401
        self._current_op = text
        # Future: if op == '非' could restrict to single input; not implemented yet.

    def operation(self) -> str:  # noqa: D401
        return self._current_op

    def set_operation(self, op_label: str):  # noqa: D401
        if op_label in self._operations:
            idx = self._operations.index(op_label)
            if idx != self._op_combo.currentIndex():
                self._op_combo.setCurrentIndex(idx)

    def _layout_sockets(self):  # noqa: D401
        if not self._in_sockets and not self._out_sockets:
            return
        w, h = self.size()
        if self._in_sockets:
            gap = h / (len(self._in_sockets) + 1)
            for idx, sock in enumerate(self._in_sockets, start=1):
                sock.setPos(-QD_NodeSocket.RADIUS, gap * idx)
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)
