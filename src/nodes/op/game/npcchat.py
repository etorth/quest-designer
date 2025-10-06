# -*- coding: utf-8 -*-
"""NPCChat operation node.

Represents an NPC dialog trigger / line in a quest flow.

Concept / Socket semantics:
  - First STRING IN socket: NPC text shown to the player.
  - Subsequent STRING IN sockets (second .. penultimate STRING before PROCESS IN): player selectable options.
  - Final IN socket: PROCESS (incoming execution flow) – activates this dialog.
  - For EVERY option STRING IN socket there is a corresponding PROCESS OUT socket (branch when that option is chosen).

Minimum socket set:
  IN[0] : STRING  (dialog text)
  IN[1] : STRING  (first option)
  IN[-1]: PROCESS (flow in)
  OUT[*]: PROCESS (one per option, >=1)

Adding/removing options keeps dialog text + >=1 option invariant; PROCESS flow IN stays at end; number of PROCESS OUT sockets always equals number of option STRING inputs.
"""
from importlib import import_module
from typing import Optional, List
from PySide6.QtWidgets import QMenu  # UPDATED: only QMenu here
from PySide6.QtGui import QAction    # UPDATED: QAction from QtGui

_qdns = import_module('qdnodesocket')
QD_NodeSocket = _qdns.QD_NodeSocket
SocketDirection = _qdns.SocketDirection
SocketType = _qdns.SocketType
_qdop = import_module('nodes.qdopnode')
QD_OpNode = _qdop.QD_OpNode

__all__ = ["NPCChat"]


class NPCChat(QD_OpNode):
    def __init__(self, title: str = "NPC对话", parent: Optional[object] = None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Build minimum: text, 1 option, flow in
        self._in_sockets = [
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.STRING),  # Dialog text
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.STRING),  # Option 1
            QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS),  # Flow in
        ]
        self._out_sockets = []  # created via sync
        self._sync_option_out_sockets()
        self._layout_sockets()

    # --- Socket role helpers --------------------------------------------
    def text_in_socket(self) -> QD_NodeSocket:
        return self._in_sockets[0]

    def option_in_sockets(self) -> List[QD_NodeSocket]:
        # All STRING sockets except the first (dialog text) and excluding the final PROCESS IN
        return [s for s in self._in_sockets[1:-1] if s.socket_type() == SocketType.STRING]

    def flow_in_socket(self) -> QD_NodeSocket:
        return self._in_sockets[-1]

    def option_out_sockets(self) -> List[QD_NodeSocket]:
        return list(self._out_sockets)

    # --- Dynamic option management --------------------------------------
    def add_option(self) -> QD_NodeSocket:
        """Append a new option STRING IN (before PROCESS IN) and matching PROCESS OUT."""
        flow_in = self._in_sockets.pop()  # remove temporarily
        new_in = QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.STRING)
        self._in_sockets.append(new_in)
        self._in_sockets.append(flow_in)
        self._sync_option_out_sockets()
        self._layout_sockets()
        return new_in

    def remove_option(self, index: int = -1) -> bool:
        """Remove an option by index in option list (default last). Returns True if removed.

        Will not remove if this would leave zero options.
        Detaches and deletes associated PROCESS OUT socket to keep mapping.
        """
        options = self.option_in_sockets()
        if not options or len(options) <= 1:
            return False  # must keep at least one option
        if index < 0:
            index = len(options) - 1
        if index >= len(options):
            return False
        target_in = options[index]
        # Remove from _in_sockets (keeping text + others + flow)
        self._detach_socket_edges(target_in)
        self._in_sockets.remove(target_in)
        target_in.setParentItem(None)
        target_in = None  # GC hint
        self._sync_option_out_sockets()
        self._layout_sockets()
        return True

    def _detach_socket_edges(self, socket: QD_NodeSocket):
        for edge in list(socket.edges()):
            try:
                scene = edge.scene()
                if scene:
                    scene.removeItem(edge)
                else:
                    edge.detach()
            except Exception:
                pass
            # Ensure bidirectional unlink
            try:
                socket.remove_edge(edge)
            except Exception:
                pass

    def _sync_option_out_sockets(self):
        """Ensure one PROCESS OUT per option STRING IN socket."""
        options = self.option_in_sockets()
        needed = len(options)
        current = len(self._out_sockets)
        # Remove extras
        while current > needed:
            sock = self._out_sockets.pop()
            self._detach_socket_edges(sock)
            if sock.scene():
                sock.scene().removeItem(sock)
            sock.setParentItem(None)
            current -= 1
        # Add missing
        while current < needed:
            self._out_sockets.append(
                QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS)
            )
            current += 1

    # --- Layout ----------------------------------------------------------
    def _layout_sockets(self):
        w, h = self.size()
        min_height = max(120, 30 * (len(self._in_sockets) + 1))
        if h < min_height:
            self._h = min_height
            w, h = self.size()
        if self._in_sockets:
            gap_in = h / (len(self._in_sockets) + 1)
            for idx, sock in enumerate(self._in_sockets, start=1):
                sock.setPos(-QD_NodeSocket.RADIUS - 1, gap_in * idx)
        options = self.option_in_sockets()
        for opt_sock, out_sock in zip(options, self._out_sockets):
            pos = opt_sock.pos()
            out_sock.setPos(w + QD_NodeSocket.RADIUS + 1, pos.y())
        self.update()

    # --- Context menu ---------------------------------------------------
    def contextMenuEvent(self, event):  # Qt override
        menu = QMenu()
        options = self.option_in_sockets()
        # Delete actions for each option (enumerated 1..N)
        for idx, _opt in enumerate(options, start=1):
            act = QAction(f"删除选项{idx}", menu)
            act.triggered.connect(lambda checked=False, i=idx - 1: self._on_remove_option(i))
            if len(options) <= 1:
                act.setEnabled(False)
            menu.addAction(act)
        add_act = QAction(f"添加选项{len(options) + 1}", menu)
        add_act.triggered.connect(self._on_add_option)
        menu.addSeparator()
        menu.addAction(add_act)
        menu.exec(event.screenPos())
        event.accept()

    def _on_add_option(self):
        self.add_option()

    def _on_remove_option(self, option_index: int):
        self.remove_option(option_index)

    # --- Overrides / hooks (if node size changes externally) ------------
    def on_geometry_changed(self):  # hypothetical hook from base when resized
        self._layout_sockets()

    # Representation helpers ---------------------------------------------
    def __repr__(self):  # noqa: D401
        return f"<NPCChat text={self.text_in_socket()} options={len(self.option_in_sockets())}>"
