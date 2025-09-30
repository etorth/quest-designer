# -*- coding: utf-8 -*-
"""Graphics scene implementation for QuestDesigner (renamed from gdgfxscene).

QD_GfxScene centralizes custom rendering / behaviors (grid, future snapping,
context menus, selection helpers, etc.). QD_MdiWindow uses this instead of a
plain QGraphicsScene so later enhancements remain localized here.
"""
from typing import Optional, Callable, Dict, TYPE_CHECKING, cast  # added cast
from PySide6.QtWidgets import QGraphicsScene, QApplication, QWidget  # Added QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QTransform
from PySide6.QtCore import QRectF, QPointF, Qt  # Added Qt

# --- New imports for edge-connecting feature ---
from qdnodesocket import QD_NodeSocket, SocketDirection, SocketType  # UPDATED import to include SocketType
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
        # NOTE: default node factories & concrete factory helpers moved to specialized subclasses.
        # --- Edge connecting state ---
        self._connecting_edge: Optional[QD_Edge] = None
        self._connecting_socket: Optional[QD_NodeSocket] = None  # start socket (IN or OUT)
        self._hover_target_socket: Optional[QD_NodeSocket] = None  # currently highlighted potential target

    # --- Palette configuration -------------------------------------------
    def set_palette(self, bg: QColor, minor: QColor, major: QColor):  # noqa: D401
        """Override the scene/grid colors on a per-instance basis."""
        self._BG_COLOR = bg
        self._GRID_MINOR = minor
        self._GRID_MAJOR = major

    # --- Node factory management -----------------------------------------
    def register_node_type(self, label: str, factory: Callable[[], 'QD_Node']):  # noqa: D401
        self._node_factories[label] = factory

    def node_factory_labels(self):  # noqa: D401
        return self._node_factories.keys()

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
    # (Handled in subclasses.)

    # --- Edge connecting interaction (enhanced) ---------------------------
    def _clear_hover_target(self):
        if self._hover_target_socket is not None:
            try:
                self._hover_target_socket.setHighlight(False)
            except Exception:  # pragma: no cover
                pass
        self._hover_target_socket = None

    @staticmethod
    def _sockets_compatible(a: QD_NodeSocket, b: QD_NodeSocket) -> bool:
        """Return True if sockets can be connected.

        Rules:
        - Must be different objects
        - Must be opposite directions (IN vs OUT)
        - Disallow INTEGER <-> STRING connections (both directions)
          (Future: extend with coercion / implicit cast rules.)
        """
        if a is b:
            return False
        if a.direction() == b.direction():
            return False
        t1 = a.socketType()
        t2 = b.socketType()
        # Block INTEGER <-> STRING in either order
        if ({t1, t2} == {SocketType.INTEGER, SocketType.STRING}):
            return False
        return True

    def mousePressEvent(self, event):  # noqa: D401
        if event.button() == Qt.MouseButton.RightButton:
            if self._connecting_edge is not None:
                self._cancel_connection()
                event.accept()
                return
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.scenePos(), QTransform())
            if self._connecting_edge is not None and self._connecting_socket is not None:
                if isinstance(item, QD_NodeSocket):
                    sock_item = cast(QD_NodeSocket, item)
                    if sock_item is self._connecting_socket:
                        event.accept()
                        return
                    if self._sockets_compatible(self._connecting_socket, sock_item):
                        self._connecting_edge.finalizeWith(sock_item)
                        self._connecting_edge.updatePath()
                        try:
                            self._connecting_socket.setHighlight(False)
                        except Exception:
                            pass
                        try:
                            sock_item.setHighlight(False)
                        except Exception:
                            pass
                        self._clear_hover_target()
                        self._connecting_edge = None
                        self._connecting_socket = None
                        event.accept()
                        return
                if self._connecting_edge is not None:
                    self._connecting_edge.updateDynamicEnd(event.scenePos())
                    event.accept()
                    return
            if isinstance(item, QD_NodeSocket) and self._connecting_edge is None:
                self._connecting_socket = cast(QD_NodeSocket, item)
                edge = QD_Edge(begin=self._connecting_socket)
                self._connecting_edge = edge
                self.addItem(edge)
                edge.updateDynamicEnd(event.scenePos())
                self._connecting_socket.setHighlight(True)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: D401
        if self._connecting_edge is not None and self._connecting_socket is not None:
            self._connecting_edge.updateDynamicEnd(event.scenePos())
            item = self.itemAt(event.scenePos(), QTransform())
            candidate = item if isinstance(item, QD_NodeSocket) else None
            if candidate and self._sockets_compatible(self._connecting_socket, candidate):
                if candidate is not self._hover_target_socket:
                    self._clear_hover_target()
                    candidate.setHighlight(True)
                    self._hover_target_socket = candidate
            else:
                if candidate is None or candidate is not self._hover_target_socket:
                    self._clear_hover_target()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: D401
        super().mouseReleaseEvent(event)

    def _delete_selected_items(self):
        selected = list(self.selectedItems())
        if not selected:
            return
        edges_to_delete: set[QD_Edge] = set()
        nodes_to_delete: list[QD_Node] = []
        for item in selected:
            if isinstance(item, QD_Edge):
                edges_to_delete.add(item)
            elif isinstance(item, QD_Node):
                nodes_to_delete.append(item)
        for node in nodes_to_delete:
            try:
                for sock in node.inputSockets():
                    for e in sock.edges():
                        edges_to_delete.add(e)
                for sock in node.outputSockets():
                    for e in sock.edges():
                        edges_to_delete.add(e)
            except Exception:
                pass
        try:
            if self._connecting_edge is not None and self._connecting_socket is not None:
                parent_node = self._connecting_socket.parentItem()
                if parent_node in nodes_to_delete:
                    self._cancel_connection()
        except Exception:
            pass
        for edge in list(edges_to_delete):
            try:
                edge.detach()
            except Exception:
                pass
            try:
                self.removeItem(edge)
            except Exception:
                pass
        for node in nodes_to_delete:
            try:
                self.removeItem(node)
            except Exception:
                pass

    def keyPressEvent(self, event):  # noqa: D401
        key = event.key()
        try:
            if key == Qt.Key.Key_Escape and self._connecting_edge is not None:
                self._cancel_connection()
                event.accept()
                return
            if key == Qt.Key.Key_Delete:
                self._delete_selected_items()
                event.accept()
                return
        except Exception:
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
                self._connecting_socket.setHighlight(False)
            except Exception:
                pass
        self._clear_hover_target()
        self._connecting_edge = None
        self._connecting_socket = None

__all__ = ["QD_GfxScene"]
