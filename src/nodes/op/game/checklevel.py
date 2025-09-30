# -*- coding: utf-8 -*-
"""CheckLeve operation node.

Represents a level condition / query node producing a boolean result.
This node now has:
- No input sockets (acts as a source)
- Exactly one OUT socket (BOOL)
"""
from importlib import import_module
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QSpinBox, QLabel

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["CheckLeve"]


class CheckLeve(QD_OpNode):
    def __init__(self, title: str = "等级", parent=None):
        # Initialize with explicit empty socket lists; only OUT socket created
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Single BOOL output (result of level comparison)
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.BOOL)]
        self._init_embedded_ui()
        self._layout_sockets()

    # NEW: build embedded widget ------------------------------------------------------
    def _init_embedded_ui(self):  # noqa: D401
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._combo = QComboBox(container)
        self._combo.addItems(["大于", "小于", "等于", "不大于", "不小于", "不等于"])  # comparison relations

        self._spin = QSpinBox(container)
        self._spin.setMinimum(0)
        self._spin.setMaximum(10_000)
        self._spin.setValue(1)
        self._spin.setFixedWidth(60)

        self._label = QLabel("级", container)
        self._label.setFixedWidth(24)

        layout.addWidget(self._combo)
        layout.addWidget(self._spin)
        layout.addWidget(self._label)
        self.set_embedded_widget(container, auto_resize=True)

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        if self._out_sockets:
            # Position OUT socket center at w + RADIUS to avoid overlap
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)
