# -*- coding: utf-8 -*-
"""KillMonster operation node.

Represents an action of killing (a) monster(s) in quest flow. Acts as a
process transformer:
- One PROCESS IN socket (incoming execution flow)
- One PROCESS OUT socket (continuation after kill)

Embedded UI:
  Monster type (QComboBox)
  Kill count (QSpinBox)
  Timeout seconds (QSpinBox)
"""
from importlib import import_module

from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QSpinBox, QLabel

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["KillMonster"]


class KillMonster(QD_OpNode):
    def __init__(self, title: str = "击杀怪物", parent: object | None = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Sockets ---------------------------------------------------------
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS)
        ]
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS)
        ]
        # Embedded UI ----------------------------------------------------
        self._init_embedded_ui()
        self._layout_sockets()

    def _init_embedded_ui(self):  # noqa: D401
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        # Monster type
        self._combo_monster = QComboBox(container)
        self._combo_monster.addItems(["骷髅", "僵尸", "蜈蚣", "鹿", "鸡", "蛇"])  # sample types
        self._combo_monster.setMinimumContentsLength(2)
        # Kill count
        self._spin_count = QSpinBox(container)
        self._spin_count.setRange(1, 9999)
        self._spin_count.setValue(1)
        self._spin_count.setFixedWidth(70)
        # Timeout seconds
        self._label_timeout = QLabel("超时", container)
        self._spin_timeout = QSpinBox(container)
        self._spin_timeout.setRange(0, 3600)
        self._spin_timeout.setValue(0)  # 0 => no timeout
        self._spin_timeout.setFixedWidth(70)
        self._label_seconds = QLabel("秒", container)
        # Assemble
        layout.addWidget(self._combo_monster)
        layout.addWidget(self._spin_count)
        layout.addWidget(self._label_timeout)
        layout.addWidget(self._spin_timeout)
        layout.addWidget(self._label_seconds)
        self.set_embedded_widget(container, auto_resize=True)

    def monster_type(self) -> str:  # noqa: D401
        return self._combo_monster.currentText()

    def kill_count(self) -> int:  # noqa: D401
        return self._spin_count.value()

    def timeout_seconds(self) -> int:  # noqa: D401
        return self._spin_timeout.value()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_h = 80
        if h < min_h:
            self._h = min_h
            w, h = self.size()
        if self._in_sockets:
            self._in_sockets[0].setPos(-QD_NodeSocket.RADIUS - 1, h / 2)
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS + 1, h / 2)

    def on_geometry_changed(self):  # hook if resized externally
        self._layout_sockets()

    def __repr__(self):  # noqa: D401
        return f"<KillMonster monster={self.monster_type()} count={self.kill_count()} timeout={self.timeout_seconds()}>"
