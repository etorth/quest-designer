# -*- coding: utf-8 -*-
"""Graphics scene implementation for QuestDesigner (renamed from gdgfxscene).

QD_GfxScene centralizes custom rendering / behaviors (grid, future snapping,
context menus, selection helpers, etc.). QD_MdiWindow uses this instead of a
plain QGraphicsScene so later enhancements remain localized here.
"""
from typing import Optional, Callable, Dict, TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsScene, QMenu
from PySide6.QtGui import QPainter, QPen, QColor, QTransform
from PySide6.QtCore import QRectF, QPointF, Qt  # Added Qt

# --- New imports for edge-connecting feature ---
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from qdedge import QD_Edge  # type: ignore
from qdnode import QD_Node  # runtime import for deletion isinstance checks

if TYPE_CHECKING:  # type-only imports to satisfy analyzer without runtime cycles
    from qdnode import QD_Node


class QD_GfxScene(QGraphicsScene):
    DEFAULT_RECT = (-2000, -2000, 4000, 4000)
    # --- Color palette (tweakable) ---
    _BG_COLOR = QColor(0x37, 0x39, 0x3f)
    _GRID_MINOR = QColor(0x43, 0x46, 0x4c)
    _GRID_MAJOR = QColor(0x54, 0x59, 0x5f)

    def __init__(self, parent=None, scene_rect: Optional[QRectF] = None, grid_step: int = 50):
        if scene_rect is None:
            x, y, w, h = self.DEFAULT_RECT
            super().__init__(x, y, w, h, parent)
        else:
            super().__init__(scene_rect, parent)
        self._grid_step = grid_step
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        self._node_factories: Dict[str, Callable[[], 'QD_Node']] = {}
        self._install_default_node_factories()
        # --- Edge connecting state ---
        self._connecting_edge: Optional[QD_Edge] = None
        self._connecting_socket: Optional[QD_NodeSocket] = None  # start socket (IN or OUT)
        self._hover_target_socket: Optional[QD_NodeSocket] = None  # currently highlighted potential target

    # --- Node factory management -----------------------------------------
    def _install_default_node_factories(self):
        self.register_node_type("Enter", self._factory_enter)
        self.register_node_type("Exit", self._factory_exit)

    def register_node_type(self, label: str, factory: Callable[[], 'QD_Node']):  # noqa: D401
        self._node_factories[label] = factory

    def node_factory_labels(self):  # noqa: D401
        return sorted(self._node_factories.keys())

    @staticmethod
    def _factory_enter():  # noqa: D401
        from nodes.state.primitives.enter import Enter  # updated path
        return Enter()

    @staticmethod
    def _factory_exit():  # noqa: D401
        from nodes.state.primitives.exit import Exit  # updated path
        return Exit()

    def _spawn_node(self, label: str, scene_pos: QPointF):
        factory = self._node_factories.get(label)
        if not factory:
            return None
        try:
            node = factory()
        except Exception:
            return None
        try:
            br = node.boundingRect()
            node.setPos(scene_pos - br.center())
        except Exception:
            node.setPos(scene_pos)
        self.addItem(node)
        for item in self.selectedItems():
            item.setSelected(False)
        node.setSelected(True)
        return node

    # --- Configuration API -------------------------------------------------
    def set_grid_step(self, step: int):
        self._grid_step = max(5, step)
        self.update()

    def grid_step(self) -> int:
        return self._grid_step

    # --- Drawing ------------------------------------------------------------
    def drawBackground(self, painter: QPainter, rect: QRectF):  # noqa: N802
        painter.fillRect(rect, self._BG_COLOR)
        step = self._grid_step
        if step <= 0:
            return
        minor_pen = QPen(self._GRID_MINOR)
        major_pen = QPen(self._GRID_MAJOR)
        for p in (minor_pen, major_pen):
            p.setWidthF(0)
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)
        right = int(rect.right())
        bottom = int(rect.bottom())
        x = left
        top_i = int(rect.top())
        bottom_i = int(rect.bottom())
        while x <= right:
            index = int(round(x / step))
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            painter.drawLine(int(x), top_i, int(x), bottom_i)
            x += step
        y = top
        left_i = int(rect.left())
        right_i = int(rect.right())
        while y <= bottom:
            index = int(round(y / step))
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            painter.drawLine(left_i, int(y), right_i, int(y))
            y += step

    # --- Context menu -----------------------------------------------------
    def contextMenuEvent(self, event):  # noqa: D401
        scene_pos = event.scenePos()
        item = self.itemAt(scene_pos, QTransform())
        if item is not None:
            return super().contextMenuEvent(event)
        menu = QMenu()
        add_menu = menu.addMenu("Add Node")
        for label in self.node_factory_labels():
            act = add_menu.addAction(label)
            act.triggered.connect(lambda _c=False, l=label, p=QPointF(scene_pos): self._spawn_node(l, p))
        menu.exec(event.screenPos())
        event.accept()

    # --- Edge connecting interaction (enhanced) ---------------------------
    def _clear_hover_target(self):
        if self._hover_target_socket is not None:
            try:
                self._hover_target_socket.set_highlight(False)
            except Exception:  # pragma: no cover
                pass
        self._hover_target_socket = None

    @staticmethod
    def _sockets_compatible(a: QD_NodeSocket, b: QD_NodeSocket) -> bool:
        if a is b:
            return False
        if a.direction() == b.direction():
            return False
        # Multi-connection enabled: do not block if sockets already have edges
        return True

    def mousePressEvent(self, event):  # noqa: D401
        # Right-click: if currently connecting, cancel instead of showing context menu
        if event.button() == Qt.MouseButton.RightButton:
            if self._connecting_edge is not None:
                self._cancel_connection()
                event.accept()
                return
        if event.button() == Qt.MouseButton.LeftButton:  # Left button
            item = self.itemAt(event.scenePos(), QTransform())
            # If we are already connecting, try to finalize on compatible socket click
            if self._connecting_edge is not None and self._connecting_socket is not None:
                if isinstance(item, QD_NodeSocket):
                    if item is self._connecting_socket:
                        # Clicking start socket again does nothing (ESC required to cancel)
                        event.accept()
                        return
                    if self._sockets_compatible(self._connecting_socket, item):
                        # Finalize
                        self._connecting_edge.finalize_with(item)
                        self._connecting_edge.update_path()
                        # Clear highlights
                        try:
                            self._connecting_socket.set_highlight(False)
                        except Exception:
                            pass
                        try:
                            item.set_highlight(False)
                        except Exception:
                            pass
                        self._clear_hover_target()
                        # Reset state
                        self._connecting_edge = None
                        self._connecting_socket = None
                        event.accept()
                        return
                # If clicked elsewhere (not a compatible socket) just update dynamic end to click point
                if self._connecting_edge is not None:
                    self._connecting_edge.update_dynamic_end(event.scenePos())
                    event.accept()
                    return
            # Not currently connecting: maybe start a new connection
            if isinstance(item, QD_NodeSocket) and self._connecting_edge is None:
                # Start provisional edge (multi-connection: no occupancy check)
                self._connecting_socket = item
                edge = QD_Edge(begin=item)
                self._connecting_edge = edge
                self.addItem(edge)
                edge.update_dynamic_end(event.scenePos())
                item.set_highlight(True)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: D401
        if self._connecting_edge is not None and self._connecting_socket is not None:
            self._connecting_edge.update_dynamic_end(event.scenePos())
            item = self.itemAt(event.scenePos(), QTransform())
            candidate = item if isinstance(item, QD_NodeSocket) else None
            if candidate and self._sockets_compatible(self._connecting_socket, candidate):
                if candidate is not self._hover_target_socket:
                    self._clear_hover_target()
                    candidate.set_highlight(True)
                    self._hover_target_socket = candidate
            else:
                if candidate is None or candidate is not self._hover_target_socket:
                    self._clear_hover_target()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: D401
        # Release no longer finalizes or cancels connections; let base handle selection, etc.
        super().mouseReleaseEvent(event)

    def _delete_selected_items(self):
        """Delete selected edges and nodes.

        Order: collect all edges (explicitly selected + those attached to selected nodes),
        detach & remove them, then remove nodes. Cancels in-progress connection if its
        start socket belongs to a node being deleted.
        """
        selected = list(self.selectedItems())
        if not selected:
            return
        edges_to_delete: set[QD_Edge] = set()
        nodes_to_delete: list[QD_Node] = []

        # Collect explicit selections
        for item in selected:
            if isinstance(item, QD_Edge):
                edges_to_delete.add(item)
            elif isinstance(item, QD_Node):
                nodes_to_delete.append(item)

        # Collect edges attached to nodes
        for node in nodes_to_delete:
            try:
                for sock in node.input_sockets():
                    for e in sock.edges():
                        edges_to_delete.add(e)
                for sock in node.output_sockets():
                    for e in sock.edges():
                        edges_to_delete.add(e)
            except Exception:  # pragma: no cover
                pass

        # If a connecting edge in progress originates from a soon-to-be-deleted node, cancel it first
        try:
            if self._connecting_edge is not None and self._connecting_socket is not None:
                parent_node = self._connecting_socket.parentItem()
                if parent_node in nodes_to_delete:
                    self._cancel_connection()
        except Exception:  # pragma: no cover
            pass

        # Remove edges
        for edge in list(edges_to_delete):
            try:
                edge.detach()
            except Exception:  # pragma: no cover
                pass
            try:
                self.removeItem(edge)
            except Exception:  # pragma: no cover
                pass

        # Remove nodes
        for node in nodes_to_delete:
            try:
                self.removeItem(node)
            except Exception:  # pragma: no cover
                pass

    def keyPressEvent(self, event):  # noqa: D401
        # ESC cancels an in-progress connection or Delete/Backspace removes selection
        key = event.key()
        try:
            if key == Qt.Key.Key_Escape and self._connecting_edge is not None:
                self._cancel_connection()
                event.accept()
                return
            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self._delete_selected_items()
                event.accept()
                return
        except Exception:  # pragma: no cover
            pass
        super().keyPressEvent(event)

    def _cancel_connection(self):
        if self._connecting_edge is not None:
            try:
                self.removeItem(self._connecting_edge)
            except Exception:  # pragma: no cover
                pass
        if self._connecting_socket is not None:
            try:
                self._connecting_socket.set_highlight(False)
            except Exception:
                pass
        self._clear_hover_target()
        self._connecting_edge = None
        self._connecting_socket = None

__all__ = ["QD_GfxScene"]
