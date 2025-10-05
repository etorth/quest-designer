# -*- coding: utf-8 -*-
"""Stringify operation node.

Converts an incoming INTEGER value to a STRING representation.
Structure only (no evaluation runtime implemented yet).

Sockets:
  IN[0]: INTEGER
  OUT[0]: STRING
"""
from importlib import import_module
from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox  # NEW imports

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Stringify"]


class Stringify(QD_OpNode):
    def __init__(self, title: str = "字符串化", parent: Optional[object] = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # One INTEGER input
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.INTEGER),
        ]
        # One STRING output
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.STRING),
        ]
        # Embedded UI
        self._combo = None  # type: QComboBox | None
        self._container = None  # type: QWidget | None
        self._init_embedded_ui()  # NEW
        self._layout_sockets()

    def _init_embedded_ui(self):  # NEW helper
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        combo = QComboBox(container)
        combo.addItems(["DECIMAL", "INTEGER", "BOOL"])  # reordered entries
        combo.currentIndexChanged.connect(self._on_type_changed)  # RESTORED connect
        lay.addWidget(combo, 1)
        self._combo = combo
        self._container = container
        # Attach to node (auto resize centers inside body region)
        try:
            self.set_embedded_widget(container, auto_resize=True)
        except Exception:
            pass

    def _current_type_name(self) -> str:  # RESTORED helper
        return self._combo.currentText() if self._combo else "INTEGER"

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_height = 60
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        # Input on left vertically centered
        in_sock = self._in_sockets[0]
        in_sock.setPos(-QD_NodeSocket.RADIUS, h / 2)
        # Output on right vertically centered
        out_sock = self._out_sockets[0]
        out_sock.setPos(w + QD_NodeSocket.RADIUS, h / 2)

    def input_socket(self) -> QD_NodeSocket:
        return self._in_sockets[0]

    def output_socket(self) -> QD_NodeSocket:
        return self._out_sockets[0]

    def _on_type_changed(self, _idx: int):  # NEW: update IN socket type dynamically
        if not self._in_sockets:
            return
        sock = self._in_sockets[0]
        mapping = {
            "INTEGER": SocketType.INTEGER,
            "DECIMAL": SocketType.DECIMAL,
            "BOOL": SocketType.BOOL,
        }
        new_type = mapping.get(self._current_type_name(), SocketType.INTEGER)
        if new_type == sock.socket_type():
            return
        # Mutate type in place; incompatible edges will be detached automatically
        try:
            sock.set_socket_type(new_type, detach_incompatible=True)
        except Exception:
            pass
        # Re-layout in case visuals depend on type (currently size same)
        self._layout_sockets()
        self.update()
