# -*- coding: utf-8 -*-
"""Logic operation node (refactored to snake_case project APIs)."""
from importlib import import_module
from PySide6.QtWidgets import QComboBox, QMenu
from PySide6.QtCore import Qt

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["Logic"]


class Logic(QD_OpNode):
    MIN_INPUTS = 2
    _MIN_SOCKET_GAP = 24  # desired minimal vertical spacing between sockets

    def __init__(self, title: str = "逻辑运算", parent=None, in_count: int = 2):
        if in_count < self.MIN_INPUTS:
            in_count = self.MIN_INPUTS
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Capture original base height so we never shrink below it
        self._base_height = self._h
        # Inputs
        self._in_sockets = [QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.BOOL) for _ in range(in_count)]
        # Output
        self._out_sockets = [QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.BOOL)]
        # Embedded logical operation selector combo
        self._op_combo = QComboBox()
        self._operations = ["与", "或", "非"]
        self._op_combo.addItems(self._operations)
        self._current_op = self._op_combo.currentText()
        self._op_combo.currentTextChanged.connect(self._on_op_changed)
        self.set_embedded_widget(self._op_combo, auto_resize=True)
        # After embedding, reset base height if embedding enlarged it
        self._base_height = self._h
        self._resize_for_socket_count()
        self._layout_sockets()

    def _on_op_changed(self, text: str):  # noqa: D401
        self._current_op = text
        if text == "非":
            self._ensure_single_input_for_not()
        else:
            # If switching FROM NOT to AND/OR, ensure we now have exactly MIN_INPUTS inputs
            if text in ("与", "或") and len(self._in_sockets) < self.MIN_INPUTS:
                # Add sockets until we reach MIN_INPUTS (typically 2)
                while len(self._in_sockets) < self.MIN_INPUTS:
                    new_sock = QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.BOOL)
                    self._in_sockets.append(new_sock)
        self._layout_sockets()

    def _ensure_single_input_for_not(self):
        """Ensure only one IN socket remains for NOT (非) operation.

        Removes all extra input sockets beyond the first, detaching and removing
        any connected edges, then re-layouts sockets and resizes node.
        """
        if len(self._in_sockets) <= 1:
            return
        # Keep first socket, remove others
        to_remove = self._in_sockets[1:]
        self._in_sockets = self._in_sockets[:1]
        for sock in to_remove:
            try:
                for edge in list(sock.edges()):  # type: ignore[attr-defined]
                    try:
                        edge.detach()
                    except Exception:
                        pass
                    try:
                        if self.scene():
                            self.scene().removeItem(edge)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if self.scene():
                    self.scene().removeItem(sock)
            except Exception:
                pass
        self._resize_for_socket_count()

    def operation(self) -> str:  # noqa: D401
        return self._current_op

    def set_operation(self, op_label: str):  # noqa: D401
        if op_label in self._operations:
            idx = self._operations.index(op_label)
            if idx != self._op_combo.currentIndex():
                self._op_combo.setCurrentIndex(idx)

    # --- Size / layout helpers -------------------------------------------
    def _resize_for_socket_count(self):
        """Adjust node height to keep reasonable spacing for current inputs."""
        n = max(1, len(self._in_sockets))
        # Need at least (n+1)*gap to distribute with top/bottom margin using gap spacing
        needed = max(self._base_height, (n + 1) * self._MIN_SOCKET_GAP)
        if needed != self._h:
            self.prepareGeometryChange()
            self._h = needed
            self._recenter_embedded_widget()
        else:
            # Height unchanged, still ensure embedded widget centered (in case width changed in future)
            self._recenter_embedded_widget()

    def _recenter_embedded_widget(self):
        """Center the embedded widget within the node rectangle.

        Centers both horizontally and vertically (including title area) to satisfy
        the requirement that the embedded widget stays centered when the node
        resizes due to socket count changes.
        """
        try:
            if not hasattr(self, '_proxy') or self._proxy is None:
                return
            widget = self._proxy.widget()
            if widget is None:
                return
            w = widget.width()
            h = widget.height()
            # Fallback to sizeHint if width/height not yet laid out
            if w <= 0 or h <= 0:
                sh = widget.sizeHint()
                w = sh.width()
                h = sh.height()
            # Center inside node rect (0,0,self._w,self._h)
            x = (self._w - w) / 2.0
            y = (self._h - h) / 2.0
            # Clamp minimum to small padding (avoid negative due to large widget)
            if x < 4:
                x = 4
            if y < 4:
                y = 4
            self._proxy.setPos(x, y)
        except Exception:
            pass

    def _layout_sockets(self):  # noqa: D401
        if not self._in_sockets and not self._out_sockets:
            return
        self._resize_for_socket_count()
        w, h = self.size()
        if self._in_sockets:
            gap = h / (len(self._in_sockets) + 1)
            for idx, sock in enumerate(self._in_sockets, start=1):
                sock.setPos(-QD_NodeSocket.RADIUS, gap * idx)
        if self._out_sockets:
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2)
        # Refresh edge paths (sockets moved)
        try:
            for sock in self._in_sockets:
                for e in sock.edges():
                    e.update_path()
            for sock in self._out_sockets:
                for e in sock.edges():
                    e.update_path()
        except Exception:
            pass
        self.update()

    # ---- Dynamic input socket management (AND/OR only) ------------------
    def _add_input_socket_dynamic(self):
        if self._current_op == "非":  # disallow adding when NOT
            return
        new_sock = QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.BOOL)
        self._in_sockets.append(new_sock)
        self._layout_sockets()

    def _remove_input_socket_dynamic(self):
        if self._current_op == "非":  # cannot remove beyond enforced single
            return
        if len(self._in_sockets) <= self.MIN_INPUTS:
            return
        sock = self._in_sockets.pop()
        try:
            for edge in list(sock.edges()):  # type: ignore[attr-defined]
                try:
                    edge.detach()
                except Exception:
                    pass
                try:
                    if self.scene():
                        self.scene().removeItem(edge)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if self.scene():
                self.scene().removeItem(sock)
        except Exception:
            pass
        self._layout_sockets()

    # ---- Context menu ---------------------------------------------------
    def contextMenuEvent(self, event):  # noqa: D401
        if self._current_op not in ("与", "或"):
            return super().contextMenuEvent(event)
        from PySide6.QtWidgets import QMenu  # local import safe
        menu = QMenu()
        add_act = menu.addAction("添加输入 (Add IN)")
        remove_act = menu.addAction("删除输入 (Remove IN)")
        if len(self._in_sockets) <= self.MIN_INPUTS:
            remove_act.setEnabled(False)
        chosen = menu.exec(event.screenPos())
        if chosen is add_act:
            self._add_input_socket_dynamic()
            event.accept()
            return
        if chosen is remove_act and remove_act.isEnabled():
            self._remove_input_socket_dynamic()
            event.accept()
            return
        super().contextMenuEvent(event)
