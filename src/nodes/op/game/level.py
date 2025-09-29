# -*- coding: utf-8 -*-
"""Level operation node.

Represents a game level operation placeholder with a single input and output
socket (e.g., sequencing levels or gating flow). Future extensions could add
properties such as difficulty, environment, or prerequisites.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QSpinBox, QLabel  # NEW imports
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from nodes.qdopnode import QD_OpNode

__all__ = ["Level"]


class Level(QD_OpNode):
    def __init__(self, title: str = "Level", parent=None):
        # Initialize with explicit empty socket lists so base validation passes
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # One input, one output
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self)]
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self)]
        # Install embedded UI (combo | non-negative number | label '级')
        self._init_embedded_ui()
        # Layout sockets AFTER embedding (node may have resized)
        self._layout_sockets()

    # NEW: build embedded widget ------------------------------------------------------
    def _init_embedded_ui(self):  # noqa: D401
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._combo = QComboBox(container)
        self._combo.addItems(["大于", "小于", "等于", "不大于", "不小于", "不等于"])  # ADDED

        self._spin = QSpinBox(container)
        self._spin.setMinimum(0)        # non-negative only
        self._spin.setMaximum(10_000)   # arbitrary upper bound
        self._spin.setValue(1)
        self._spin.setFixedWidth(60)

        self._label = QLabel("级", container)
        # Give label a larger fixed width for readability/alignment
        self._label.setFixedWidth(24)

        layout.addWidget(self._combo)
        layout.addWidget(self._spin)
        layout.addWidget(self._label)
        # Embed inside node; auto_resize so node adjusts to content
        self.setEmbeddedWidget(container, auto_resize=True)

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        # Input on left middle, output on right middle
        if self._in_sockets:
            self._in_sockets[0].setPos(0, h / 2)
        if self._out_sockets:
            self._out_sockets[0].setPos(w, h / 2)
