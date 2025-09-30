# -*- coding: utf-8 -*-
"""Compare operation node.

Provides a comparison operation selection with at least two input sockets and
one output socket. Operations: 大于, 小于, 等于, 不大于, 不小于, 不等于.

Future enhancements:
- Dynamic type hints for inputs
- Constant folding when both inputs are literals
- Auto inversion / swapping utilities
"""
from PySide6.QtWidgets import QComboBox
from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType  # UPDATED import
from nodes.qdopnode import QD_OpNode

__all__ = ["Compare"]


class Compare(QD_OpNode):
    MIN_INPUTS = 2

    def __init__(self, title: str = "比较运算", parent=None, in_count: int = 2):
        if in_count < self.MIN_INPUTS:
            in_count = self.MIN_INPUTS
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Inputs (two or more) numeric
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.DECIMAL) for _ in range(in_count)]
        # Single output boolean result
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.BOOL)]
        # Embedded comparison operation selector
        self._op_combo = QComboBox()
        self._operations = ["大于", "小于", "等于", "不大于", "不小于", "不等于"]
        self._op_combo.addItems(self._operations)
        self._current_op = self._op_combo.currentText()
        self._op_combo.currentTextChanged.connect(self._on_op_changed)
        self.setEmbeddedWidget(self._op_combo, auto_resize=True)
        self._layout_sockets()

    def _on_op_changed(self, text: str):  # noqa: D401
        self._current_op = text
        # Future: validation or propagation when comparison changes

    def operation(self) -> str:  # noqa: D401
        return self._current_op

    def setOperation(self, op_label: str):  # noqa: D401
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
                sock.setPos(0, gap * idx)
        if self._out_sockets:
            self._out_sockets[0].setPos(w, h / 2)
