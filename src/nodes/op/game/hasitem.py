# -*- coding: utf-8 -*-
"""HasItem operation node.

Represents a condition check or operation that determines whether the player
(or another entity) possesses a particular item. For now this is a structural
placeholder node with one input and one output socket. Future enhancements
could add an embedded UI (e.g., item selector combo, quantity spin box).
"""
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from nodes.qdopnode import QD_OpNode
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QSpinBox, QLabel  # NEW imports

__all__ = ["HasItem"]


class HasItem(QD_OpNode):
    def __init__(self, title: str = "物品", parent=None):
        # Initialize base with explicit empty socket lists so we can construct manually
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # One input (flow comes in) and one output (flow continues if condition passes)
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self)]
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self)]
        # Build embedded UI phrase: 拥有 <relation> <count> 个 <item>
        self._init_embedded_ui()
        # Layout sockets after potential resize
        self._layout_sockets()

    def _init_embedded_ui(self):  # noqa: D401 NEW
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label_have = QLabel("拥有", container)

        self._combo_relation = QComboBox(container)
        self._relations = ["多于", "少于", "等于", "不多于", "不少于", "不等于"]
        self._combo_relation.addItems(self._relations)

        self._spin_count = QSpinBox(container)
        self._spin_count.setMinimum(0)
        self._spin_count.setMaximum(999999)
        self._spin_count.setValue(1)
        self._spin_count.setFixedWidth(70)

        self._label_ge = QLabel("个", container)

        self._combo_item = QComboBox(container)
        self._items = ["太阳水", "木剑", "苹果"]
        self._combo_item.addItems(self._items)

        # Adjust widths to keep phrase compact while readable
        self._combo_relation.setMinimumContentsLength(3)
        self._combo_item.setMinimumContentsLength(2)
        self._combo_relation.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._combo_item.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        layout.addWidget(self._label_have)
        layout.addWidget(self._combo_relation)
        layout.addWidget(self._spin_count)
        layout.addWidget(self._label_ge)
        layout.addWidget(self._combo_item)

        self.setEmbeddedWidget(container, auto_resize=True)

    def relation(self) -> str:  # noqa: D401 NEW helper
        return self._combo_relation.currentText()

    def item_name(self) -> str:  # noqa: D401 NEW helper
        return self._combo_item.currentText()

    def count(self) -> int:  # noqa: D401 NEW helper
        return self._spin_count.value()

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        if self._in_sockets:
            self._in_sockets[0].setPos(0, h / 2)
        if self._out_sockets:
            self._out_sockets[0].setPos(w, h / 2)
