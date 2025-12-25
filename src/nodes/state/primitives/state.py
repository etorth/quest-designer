# -*- coding: utf-8 -*-
"""Primitive 'State' node.

Represents a basic state in the quest graph. It has:
- 1 input socket (PROCESS type) by default
- N output sockets (PROCESS type) where N = number of Exit nodes in the corresponding state graph

Inherits from QD_StateNode (state-layer semantic base).
"""

from ...qdstatenode import QD_StateNode
from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType

__all__ = ["State"]


class State(QD_StateNode):
    def __init__(self, title: str = "State", parent=None):
        super().__init__(title=title, parent=parent, in_sockets=[], out_sockets=[])
        # Create 1 IN socket (PROCESS type)
        in_socket = QD_NodeSocket(SocketDirection.IN, parent=self, sock_type=SocketType.PROCESS)
        self._in_sockets = [in_socket]
        # Start with 1 OUT socket by default; will be updated based on Exit nodes
        out_socket = QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS)
        self._out_sockets = [out_socket]
        self._layout_sockets()

    def update_exit_count(self, exit_count: int):
        """Update the number of OUT sockets to match the number of Exit nodes in the op graph.
        
        Args:
            exit_count: Number of Exit nodes in the corresponding state graph
        """
        if exit_count < 1:
            exit_count = 1  # At least 1 output socket
        
        current_count = len(self._out_sockets)
        
        if exit_count == current_count:
            return  # No change needed
        
        # Remove excess sockets
        while len(self._out_sockets) > exit_count:
            socket = self._out_sockets.pop()
            # Disconnect any edges
            for edge in list(socket.edges()):
                if edge.scene():
                    edge.scene().removeItem(edge)
                else:
                    edge.detach()
            # Remove socket from scene
            if socket.scene():
                socket.scene().removeItem(socket)
        
        # Add new sockets
        while len(self._out_sockets) < exit_count:
            new_socket = QD_NodeSocket(SocketDirection.OUT, parent=self, sock_type=SocketType.PROCESS)
            self._out_sockets.append(new_socket)
        
        # Resize node height to accommodate sockets with proper spacing
        self._resize_for_sockets()
        
        # Relayout sockets
        self._layout_sockets()
        
        # Update all connected edges after resize
        self._update_connected_edges()
        
        self.update()

    def _resize_for_sockets(self):
        """Resize node height to properly accommodate all OUT sockets."""
        num_out = len(self._out_sockets)
        if num_out <= 1:
            # For 0 or 1 socket, use default height
            min_height = 70
        else:
            # Calculate height needed for proper socket spacing
            # Minimum spacing between sockets: 30px
            min_spacing = 30
            # Add padding at top and bottom: 20px each
            padding = 20
            needed_height = num_out * min_spacing + padding * 2
            min_height = max(70, needed_height)
        
        if self._h != min_height:
            try:
                self.prepareGeometryChange()
            except Exception:
                pass
            self._h = min_height

    def _update_connected_edges(self):
        """Update all edges connected to this node's sockets."""
        # Update edges from IN socket
        if self._in_sockets:
            for edge in self._in_sockets[0].edges():
                try:
                    edge.update_path()
                except Exception:
                    pass
        
        # Update edges from all OUT sockets
        for socket in self._out_sockets:
            for edge in socket.edges():
                try:
                    edge.update_path()
                except Exception:
                    pass

    def _layout_sockets(self):
        w, h = self.size()
        # Position IN socket on left edge, centered vertically
        if self._in_sockets:
            self._in_sockets[0].setPos(-QD_NodeSocket.RADIUS, h / 2.0)
        
        # Position OUT sockets on right edge, distributed vertically
        num_out = len(self._out_sockets)
        if num_out == 0:
            return
        
        if num_out == 1:
            # Single socket centered
            self._out_sockets[0].setPos(w + QD_NodeSocket.RADIUS, h / 2.0)
        else:
            # Multiple sockets: evenly distributed
            spacing = h / (num_out + 1)
            for i, socket in enumerate(self._out_sockets):
                y = spacing * (i + 1)
                socket.setPos(w + QD_NodeSocket.RADIUS, y)

