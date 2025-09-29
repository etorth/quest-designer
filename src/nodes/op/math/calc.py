# -*- coding: utf-8 -*-
"""Calc operation node.

A simple math operation node placeholder. It provides:
- At least two input sockets (IN)
- One output socket (OUT)

Future extensions could let this node specify an arithmetic operation
(add, sub, mul, div, custom script) and perform validation or constant
folding. For now it is purely a structural/demo node.
"""

from PySide6.QtWidgets import QComboBox  # NEW import for embedded widget
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from nodes.qdopnode import QD_OpNode  # base op node

__all__ = ["Calc"]


class Calc(QD_OpNode):
    MIN_INPUTS = 2

    def __init__(self, title: str = "Calc", parent=None, in_count: int = 2):
        if in_count < self.MIN_INPUTS:
            in_count = self.MIN_INPUTS
        # Initialize base with empty socket lists; we'll add sockets manually
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Create input sockets
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self) for _ in range(in_count)]
        # Single output socket
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self)]
        # Embedded operation selector combo (Chinese labels: 加, 减, 乘, 除)
        self._op_combo = QComboBox()
        self._operations = ["加", "减", "乘", "除"]
        self._op_combo.addItems(self._operations)
        # Optional: store current operation symbol string in attribute
        self._current_op = self._op_combo.currentText()
        self._op_combo.currentTextChanged.connect(self._on_op_changed)
        # Embed the combo box; node may resize to fit
        self.setEmbeddedWidget(self._op_combo, auto_resize=True)
        # Layout sockets AFTER potential resize from embedding
        self._layout_sockets()

    def _on_op_changed(self, text: str):  # noqa: D401
        self._current_op = text
        # Future: trigger downstream recomputation / dirty flag

    # Convenience API (NEW)
    def operation(self) -> str:  # noqa: D401
        return self._current_op

    def setOperation(self, op_label: str):  # noqa: D401
        if op_label in self._operations:
            idx = self._operations.index(op_label)
            if idx != self._op_combo.currentIndex():
                self._op_combo.setCurrentIndex(idx)
        else:
            # Silently ignore invalid label; could raise ValueError
            pass

    # Simple vertical layout for inputs on left, single output on right middle
    def _layout_sockets(self):  # noqa: D401
        if not self._in_sockets and not self._out_sockets:
            return
        w, h = self.size()
        # Position input sockets evenly along left edge (center of each half-circle flush)
        if self._in_sockets:
            gap = h / (len(self._in_sockets) + 1)
            for idx, sock in enumerate(self._in_sockets, start=1):
                sock.setPos(0, gap * idx)
        # Output socket centered vertically on right edge
        if self._out_sockets:
            out_sock = self._out_sockets[0]
            out_sock.setPos(w, h / 2)
