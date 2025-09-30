# -*- coding: utf-8 -*-
"""Input operation node.

A simple source node producing a literal value.
- No IN sockets
- One OUT socket whose data type matches the combo selection (BOOL by default)

Combo supports: BOOL, INTEGER, DECIMAL, STRING.
Changing the type rebuilds both the OUT socket (disconnecting any incompatible edges)
AND the value-entry widget:
  BOOL     -> QComboBox(true/false)
  INTEGER  -> QSpinBox(0..9_999_999)
  DECIMAL  -> QLineEdit (QDoubleValidator + visual invalid feedback)
  STRING   -> QTextEdit (multi-line free text)

Enhancements implemented:
  (2) Validation feedback: DECIMAL field shows red border while text is invalid.
  (5) Edge persistence: Existing outgoing edges are preserved if the new type
      remains compatible with each connected IN socket; incompatible edges are removed.
"""
from importlib import import_module
from typing import Optional, Any
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLineEdit, QSpinBox, QTextEdit  # ADDED QTextEdit
from PySide6.QtGui import QDoubleValidator, QFontMetrics  # UPDATED imports
from PySide6.QtGui import QValidator  # NEW import for state comparison

# Import private layout constants for accurate auto-resize (safe local use)
try:  # pragma: no cover - defensive import
    from qdnode import _TITLE_BAR_HEIGHT as _NODE_TITLE_BAR_HEIGHT, _CONTENT_PADDING as _NODE_CONTENT_PADDING  # type: ignore
except Exception:  # fallback defaults
    _NODE_TITLE_BAR_HEIGHT = 22
    _NODE_CONTENT_PADDING = 6

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
socket_data_type_match = _qdns.socket_data_type_match  # NEW import for edge compatibility
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Input"]


class Input(QD_OpNode):
    def __init__(self, title: str = "输入", parent: Optional[object] = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # OUT socket now starts as BOOL to match default combo selection
        self._out_sockets = [
            QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.BOOL)
        ]
        # NEW: record base minimum size to allow safe shrinking later
        self._base_min_w = self._w
        self._base_min_h = self._h
        self._value_widget: QWidget | None = None  # dynamic second widget
        self._value_layout: QHBoxLayout | None = None
        self._combo_type: QComboBox | None = None
        self._container: QWidget | None = None  # NEW: store embedded container
        self._init_embedded_ui()
        self._layout_sockets()

    def _init_embedded_ui(self):  # noqa: D401
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._value_layout = layout
        self._combo_type = QComboBox(container)
        self._combo_type.addItems(["BOOL", "INTEGER", "DECIMAL", "STRING"])
        self._combo_type.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self._combo_type)
        # Set default selection to BOOL (was STRING before); rebuild value widget accordingly
        self._combo_type.setCurrentText("BOOL")
        self._rebuild_value_widget()
        self._container = container
        self.set_embedded_widget(self._container, auto_resize=True)

    # --- Value widget management ----------------------------------------
    def _current_type_name(self) -> str:
        return self._combo_type.currentText() if self._combo_type else "STRING"

    def _grab_current_value(self) -> Any:
        if self._value_widget is None:
            return None
        if isinstance(self._value_widget, QLineEdit):
            return self._value_widget.text()
        if isinstance(self._value_widget, QTextEdit):  # NEW support
            return self._value_widget.toPlainText()
        if isinstance(self._value_widget, QSpinBox):
            return self._value_widget.value()
        if isinstance(self._value_widget, QComboBox):
            return self._value_widget.currentText()
        return None

    def _rebuild_value_widget(self):
        prev_value = self._grab_current_value()
        # Remove old widget
        if self._value_widget is not None and self._value_layout is not None:
            try:
                self._value_layout.removeWidget(self._value_widget)
                self._value_widget.setParent(None)
            except Exception:
                pass
            self._value_widget = None
        tname = self._current_type_name()
        # Create new widget per type
        if tname == "BOOL":
            cb = QComboBox()
            cb.addItems(["true", "false"])
            # Preserve previous boolean-ish value if possible
            if isinstance(prev_value, str):
                low = prev_value.lower()
                if low in ("true", "false"):
                    cb.setCurrentText(low)
            self._value_widget = cb
        elif tname == "INTEGER":
            sp = QSpinBox()
            sp.setRange(0, 9_999_999)
            try:
                if isinstance(prev_value, int):
                    sp.setValue(prev_value)
                elif isinstance(prev_value, str) and prev_value.isdigit():
                    sp.setValue(int(prev_value))
            except Exception:
                pass
            self._value_widget = sp
        elif tname == "DECIMAL":
            le = QLineEdit()
            validator = QDoubleValidator(-1e12, 1e12, 8, le)
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            le.setValidator(validator)
            le.setPlaceholderText("0.0")
            if isinstance(prev_value, (int, float)):
                le.setText(str(prev_value))
            elif isinstance(prev_value, str):
                le.setText(prev_value)
            le.textChanged.connect(self._on_decimal_text_changed)  # NEW
            self._value_widget = le
        else:  # STRING -> use QTextEdit instead of QLineEdit
            te = QTextEdit()
            try:
                te.setPlaceholderText("输入文本...")
            except Exception:
                pass
            if prev_value is not None:
                te.setPlainText(str(prev_value))
            # Keep QTextEdit compact in height
            te.setFixedHeight(60)
            self._value_widget = te
        # Add new widget to layout
        if self._value_layout is not None and self._value_widget is not None:
            self._value_layout.addWidget(self._value_widget, 1)
        # NEW: auto size the value widget based on its type/content
        self._autosize_value_widget()
        self._auto_resize_after_value_change()
        self.update()

    def _autosize_value_widget(self):  # NEW helper
        """Auto shrink/expand the second widget based on current type.

        Applied only when type changes (not on every keystroke) to satisfy the
        requirement: on type switch, adjust size of the value entry control.
        """
        w = self._value_widget
        if w is None:
            return
        type_name = self._current_type_name()
        # Base width from sizeHint
        try:
            hint_w = max(40, w.sizeHint().width())
        except Exception:
            hint_w = 80
        # Strategy per type
        if type_name == "BOOL":
            # Very small combo
            w.setFixedWidth(hint_w)
        elif type_name == "INTEGER":
            # Spin box typical width
            w.setFixedWidth(hint_w)
        elif type_name == "DECIMAL":
            # Allow a bit more width; clamp
            w.setFixedWidth(min(160, max(90, hint_w)))
        elif type_name == "STRING":
            # QTextEdit: set a comfortable width (content aware heuristics)
            if isinstance(w, QTextEdit):
                doc_text = w.toPlainText() or "示例"
                fm = QFontMetrics(w.font())
                est = fm.horizontalAdvance(doc_text[:30]) + 24  # padding
                target = min(360, max(140, est))
                w.setFixedWidth(target)
        # Ask layout to recompute
        try:
            if self._container:
                self._container.updateGeometry()
        except Exception:
            pass

    def _auto_resize_after_value_change(self):  # NEW helper
        if self._container is None:
            return
        # Let layout compute size
        self._container.adjustSize()
        hint = self._container.sizeHint()
        padding = _NODE_CONTENT_PADDING
        needed_w = hint.width() + padding * 2
        needed_h = _NODE_TITLE_BAR_HEIGHT + hint.height() + padding
        # Allow shrinking: clamp to recorded base minimums
        desired_w = max(self._base_min_w, needed_w)
        desired_h = max(self._base_min_h, needed_h)
        size_changed = (desired_w != self._w) or (desired_h != self._h)
        if size_changed:
            try:
                self.prepareGeometryChange()
            except Exception:
                pass
            self._w = desired_w
            self._h = desired_h
        # Recenter existing proxy widget (using base class helper) if available
        try:
            self._center_embedded_widget_in_body(padding)
        except Exception:
            pass
        # Re-layout socket after size change
        self._layout_sockets()

    # --- Validation feedback --------------------------------------------
    def _on_decimal_text_changed(self, text: str):  # noqa: D401 NEW
        # Apply visual invalid feedback while user types invalid decimal
        if not isinstance(self._value_widget, QLineEdit):
            return
        le: QLineEdit = self._value_widget
        validator = le.validator()
        if validator is None:
            le.setStyleSheet("")
            return
        # Unpack validator state safely
        state, _txt, _pos = validator.validate(text, 0)
        if text == "":  # neutral state
            le.setStyleSheet("")
        elif state != QValidator.State.Acceptable:
            le.setStyleSheet("QLineEdit{border:1px solid #d44;}")
        else:
            le.setStyleSheet("")

    # --- Type / socket logic --------------------------------------------
    def _on_type_changed(self, _index: int):  # noqa: D401
        # First rebuild value widget for new type (handles UI + resize)
        self._rebuild_value_widget()
        # Then update socket type
        if not self._out_sockets:
            return
        current_socket = self._out_sockets[0]
        type_map = {
            "STRING": SocketType.STRING,
            "INTEGER": SocketType.INTEGER,
            "DECIMAL": SocketType.DECIMAL,
            "BOOL": SocketType.BOOL,
        }
        new_type = type_map.get(self._current_type_name(), SocketType.STRING)
        if new_type == current_socket.socket_type():
            return
        # Gather existing edges for reconnection attempt
        existing_edges = list(current_socket.edges())
        # Remove old socket graphics item AFTER capturing edges
        try:
            if current_socket.scene():
                current_socket.scene().removeItem(current_socket)
        except Exception:
            pass
        replacement = QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=new_type)
        self._out_sockets[0] = replacement
        # Reconnect compatible edges; drop incompatible ones
        for edge in existing_edges:
            try:
                # Identify the opposite (IN) socket on this edge
                other = edge.begin_socket() if edge.begin_socket() is not current_socket else edge.end_socket()
                if other is None or other.direction() != SocketDirection.IN:
                    # Edge not in a valid state for reconnection; remove
                    if edge.scene():
                        edge.scene().removeItem(edge)
                    continue
                if socket_data_type_match(replacement, other):
                    # Reattach edge to new socket preserving orientation
                    if edge.begin_socket() is current_socket:
                        edge.set_begin_socket(replacement)
                    else:
                        edge.set_end_socket(replacement)
                else:
                    # Incompatible -> remove
                    if edge.scene():
                        edge.scene().removeItem(edge)
            except Exception:
                try:
                    if edge.scene():
                        edge.scene().removeItem(edge)
                except Exception:
                    pass
        self._layout_sockets()
        self.update()

    # --- Layout ----------------------------------------------------------
    def _layout_sockets(self):  # noqa: D401
        w, h = self.size()
        min_h = 60
        if h < min_h:
            self._h = min_h
            w, h = self.size()
        if self._out_sockets:
            self._out_sockets[0].setPos(self._w + QD_NodeSocket.RADIUS, self._h / 2)  # use updated size

    def out_socket(self) -> QD_NodeSocket:  # noqa: D401
        return self._out_sockets[0]
