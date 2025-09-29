# -*- coding: utf-8 -*-
"""Function operation node.

Single-input, single-output node applying a unary mathematical function.
The function itself is not executed yet (this is a structural / UI element),
but future logic could evaluate or serialize the chosen function.

Differences vs Calc:
- Only ONE input socket.
- Combo box lists common unary functions: sin, cos, tan, asin, acos, atan,
  sinh, cosh, tanh, exp, log, log10, sqrt, abs, floor, ceil, round.
"""
from PySide6.QtWidgets import QComboBox
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from ...qdopnode import QD_OpNode  # CHANGED to relative import

__all__ = ["Function"]


class Function(QD_OpNode):
    def __init__(self, title: str = "数值函数", parent=None):
        # Initialize with empty socket lists; we construct manually
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Exactly one input and one output
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self)]
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self)]
        # Embedded combo for function selection
        self._func_combo = QComboBox()
        self._functions = [
            "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "exp", "log", "log10",
            "sqrt", "abs", "floor", "ceil", "round",
        ]
        self._func_combo.addItems(self._functions)
        self._current_func = self._func_combo.currentText()
        self._func_combo.currentTextChanged.connect(self._on_func_changed)
        self.setEmbeddedWidget(self._func_combo, auto_resize=True)
        self._layout_sockets()

    def _on_func_changed(self, text: str):  # noqa: D401
        self._current_func = text
        # Future: trigger recomputation / validation

    def function(self) -> str:  # noqa: D401
        return self._current_func

    def setFunction(self, func_label: str):  # noqa: D401
        if func_label in self._functions:
            idx = self._functions.index(func_label)
            if idx != self._func_combo.currentIndex():
                self._func_combo.setCurrentIndex(idx)

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        # Single input centered vertically on left edge
        if self._in_sockets:
            self._in_sockets[0].setPos(0, h / 2)
        # Single output centered vertically on right edge
        if self._out_sockets:
            self._out_sockets[0].setPos(w, h / 2)
