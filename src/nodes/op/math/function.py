# -*- coding: utf-8 -*-
"""Function operation node (refactored to snake_case)."""
from importlib import import_module
from PySide6.QtWidgets import QComboBox

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Function"]


class Function(QD_OpNode):
    def __init__(self, title: str = "数值函数", parent=None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.DECIMAL)]
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.DECIMAL)]
        self._func_combo = QComboBox()
        self._functions = [
            "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "exp", "log", "log10",
            "sqrt", "abs", "floor", "ceil", "round",
        ]
        self._func_combo.addItems(self._functions)
        self._current_func = self._func_combo.currentText()
        self._func_combo.currentTextChanged.connect(self._on_func_changed)
        self.set_embedded_widget(self._func_combo, auto_resize=True)
        self._layout_sockets()

    def _on_func_changed(self, text: str):
        self._current_func = text

    def function(self) -> str:
        return self._current_func

    def set_function(self, func_label: str):
        if func_label in self._functions:
            idx = self._functions.index(func_label)
            if idx != self._func_combo.currentIndex():
                self._func_combo.setCurrentIndex(idx)

    def _layout_sockets(self):
        w, h = self.size()
        if self._in_sockets:
            self._in_sockets[0].setPos(-QD_NodeSocket.RADIUS, h / 2)
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)
