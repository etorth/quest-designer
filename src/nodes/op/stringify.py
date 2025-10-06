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
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLineEdit  # UPDATED imports

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Stringify", "validate_decimal_format"]


def validate_decimal_format(fmt: str) -> bool:
    """Return True if ``fmt`` can format a decimal value using ``%`` operator.

    The validation rule: attempt ``fmt % 12.345``; if it raises any exception,
    the format string is considered invalid.
    Leading/trailing whitespace is preserved (not stripped) to let caller decide.
    ``None`` or empty string returns False (empty is not a valid percent format for a number).
    """
    if fmt is None:
        return False
    try:
        _ = fmt % 12.345
        return True
    except Exception:
        return False


class Stringify(QD_OpNode):
    def __init__(self, title: str = "字符串化", parent: Optional[object] = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # One INTEGER input
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.DECIMAL),
        ]
        # One STRING output
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.STRING),
        ]
        self._combo = None  # type: QComboBox | None
        self._container = None  # type: QWidget | None
        self._format_edit = None  # type: QLineEdit | None
        self._saved_format_str = "%f"  # NEW: persist user format across type toggles
        self._bool_repr_combo = None  # NEW: optional bool representation combo
        self._saved_bool_repr = "1/0"  # default representation saved
        self._init_embedded_ui()
        self._layout_sockets()

    # --- Embedded UI -----------------------------------------------------
    def _init_embedded_ui(self):  # NEW helper
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        combo = QComboBox(container)
        combo.addItems(["DECIMAL", "INTEGER", "BOOL"])  # reordered entries
        combo.currentIndexChanged.connect(self._on_type_changed)
        lay.addWidget(combo, 0)
        self._combo = combo
        self._container = container
        self._ensure_format_edit()  # initial (DECIMAL by default)
        try:
            self.set_embedded_widget(container, auto_resize=True)
        except Exception:
            pass

    def _ensure_format_edit(self):  # NEW helper
        if self._combo is None or self._container is None:
            return
        if self._current_type_name() != "DECIMAL":
            # When leaving DECIMAL mode remove format edit
            if self._format_edit is not None:
                # Persist current text before removal
                try:
                    self._saved_format_str = self._format_edit.text() or self._saved_format_str
                except Exception:
                    pass
                try:
                    self._format_edit.setParent(None)
                except Exception:
                    pass
                self._format_edit = None
            return
        # Need DECIMAL format edit; recreate if missing using saved text
        if self._format_edit is None:
            fe = QLineEdit(self._container)
            fe.setText(self._saved_format_str)
            fe.setMaximumWidth(100)
            fe.textChanged.connect(self._on_format_changed)  # connect validation
            # Insert after combo
            layout = self._container.layout()
            if layout is not None:
                layout.addWidget(fe)  # removed stretch argument
            self._format_edit = fe
            # initial validation
            self._on_format_changed(self._format_edit.text())

    def _ensure_bool_repr_combo(self):  # NEW helper
        """Ensure the BOOL representation combo exists only in BOOL mode."""
        if self._combo is None or self._container is None:
            return
        layout = self._container.layout()
        is_bool_mode = self._current_type_name() == "BOOL"
        if not is_bool_mode:
            if self._bool_repr_combo is not None:
                try:
                    self._saved_bool_repr = self._bool_repr_combo.currentText() or self._saved_bool_repr
                except Exception:
                    pass
                try:
                    self._bool_repr_combo.setParent(None)
                except Exception:
                    pass
                self._bool_repr_combo = None
            return
        # BOOL mode: create if missing
        if self._bool_repr_combo is None:
            combo = QComboBox(self._container)
            combo.addItems(["1/0", "true/false", "True/False", "TRUE/FALSE", "真/假"])
            # restore saved if present
            idx = combo.findText(self._saved_bool_repr)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            layout.addWidget(combo)  # removed stretch argument
            self._bool_repr_combo = combo
        else:
            # ensure order/layout stable; nothing else needed
            pass

    def _on_format_changed(self, text: str):
        """Validate decimal format string live and color background if invalid.
        Valid: clear custom background and remember string.
        Invalid: set light red background.
        """
        if self._format_edit is None:
            return
        ok = validate_decimal_format(text)
        if ok:
            # remember good format
            self._saved_format_str = text
            self._format_edit.setStyleSheet("")
        else:
            self._format_edit.setStyleSheet("background-color: rgb(255, 180, 180);")

    def _current_type_name(self) -> str:  # RESTORED helper
        return self._combo.currentText() if self._combo else "INTEGER"

    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_height = 60
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        in_sock = self._in_sockets[0]
        in_sock.setPos(-QD_NodeSocket.RADIUS, h / 2)
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
        if new_type != sock.socket_type():
            try:
                sock.set_socket_type(new_type, detach_incompatible=True)
            except Exception:
                pass
        # Update DECIMAL format editor and BOOL representation combo
        self._ensure_format_edit()
        self._ensure_bool_repr_combo()
        self._layout_sockets()
        self.update()
