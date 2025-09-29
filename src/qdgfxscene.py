# -*- coding: utf-8 -*-
"""Graphics scene implementation for QuestDesigner (renamed from gdgfxscene).

QD_GfxScene centralizes custom rendering / behaviors (grid, future snapping,
context menus, selection helpers, etc.). QD_MdiWindow uses this instead of a
plain QGraphicsScene so later enhancements remain localized here.
"""
from typing import Optional, Callable, Dict, TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsScene, QMenu
from PySide6.QtGui import QPainter, QPen, QColor, QTransform
from PySide6.QtCore import QRectF, QPointF

# --- New imports for edge-connecting feature ---
from qdnodesocket import QD_NodeSocket, SocketDirection  # type: ignore
from qdedge import QD_Edge  # type: ignore

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
        from nodes.primitives.enter import Enter  # type: ignore
        return Enter()

    @staticmethod
    def _factory_exit():  # noqa: D401
        from nodes.primitives.exit import Exit  # type: ignore
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
        # single-connection policy: both must be free
        if a.is_occupied() or b.is_occupied():
            return False
        return True

    def mousePressEvent(self, event):  # noqa: D401
        if event.button() == 1:  # Left button
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, QD_NodeSocket) and self._connecting_edge is None:
                # enforce single-connection: refuse if occupied
                if item.is_occupied():
                    event.ignore()
                    return
                # Start provisional edge from this socket
                self._connecting_socket = item
                edge = QD_Edge(begin=item)
                self._connecting_edge = edge
                self.addItem(edge)
                edge.update_dynamic_end(event.scenePos())
                item.set_highlight(True)  # indicate active
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: D401
        if self._connecting_edge is not None and self._connecting_socket is not None:
            self._connecting_edge.update_dynamic_end(event.scenePos())
            # Determine potential target under cursor
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

    def _finalize_connection_if_valid(self, release_pos: QPointF) -> bool:
        item = self.itemAt(release_pos, QTransform())
        if not isinstance(item, QD_NodeSocket):
            return False
        if self._connecting_socket is None or self._connecting_edge is None:
            return False
        target = item
        if not self._sockets_compatible(self._connecting_socket, target):
            return False
        # Finalize edge
        self._connecting_edge.finalize_with(target)
        # Ensure orientation / path updated
        self._connecting_edge.update_path()
        return True

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

    def mouseReleaseEvent(self, event):  # noqa: D401
        if self._connecting_edge is not None:
            success = self._finalize_connection_if_valid(event.scenePos())
            # clear start socket highlight either way
            if self._connecting_socket:
                try:
                    self._connecting_socket.set_highlight(False)
                except Exception:
                    pass
            self._clear_hover_target()
            if not success:
                # remove provisional edge if not completed
                self._cancel_connection()
            else:
                # keep edge; reset connection state
                self._connecting_edge = None
                self._connecting_socket = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):  # noqa: D401
        # Allow Escape to cancel an in-progress connection
        try:
            from PySide6.QtCore import Qt as _Qt
            if event.key() == _Qt.Key.Key_Escape and self._connecting_edge is not None:
                self._cancel_connection()
                event.accept()
                return
        except Exception:  # pragma: no cover - defensive
            pass
        super().keyPressEvent(event)

__all__ = ["QD_GfxScene"]
