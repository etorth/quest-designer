# -*- coding: utf-8 -*-
"""Graphics scene implementation for QuestDesigner.

QD_GfxScene centralizes custom rendering / behaviors (grid, future snapping,
context menus, selection helpers, etc.). QD_MdiWindow uses this instead of a
plain QGraphicsScene so later enhancements remain localized here.
"""

from typing import Optional, Callable, Dict, TYPE_CHECKING  # added TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsScene, QMenu
from PySide6.QtGui import QPainter, QPen, QColor, QTransform
from PySide6.QtCore import QRectF, QPointF

if TYPE_CHECKING:  # type-only imports to satisfy analyzer without runtime cycles
    from qdnode import QD_Node


class QD_GfxScene(QGraphicsScene):
    DEFAULT_RECT = (-2000, -2000, 4000, 4000)
    # --- Color palette (tweakable) ---
    # Lightened background (was 2f3136). Slightly higher luminance for contrast with darker nodes.
    _BG_COLOR = QColor(0x37, 0x39, 0x3f)          # lighter neutral grey
    _GRID_MINOR = QColor(0x43, 0x46, 0x4c)        # adjusted to stay subtle over lighter bg
    _GRID_MAJOR = QColor(0x54, 0x59, 0x5f)        # slightly brighter major lines

    def __init__(self, parent=None, scene_rect: Optional[QRectF] = None, grid_step: int = 50):
        # Initialize base scene rectangle (mirrors previous hard‑coded values)
        if scene_rect is None:
            x, y, w, h = self.DEFAULT_RECT
            super().__init__(x, y, w, h, parent)
        else:
            super().__init__(scene_rect, parent)
        self._grid_step = grid_step
        # Disable indexing for potentially dynamic many-item scenes (faster inserts)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # Node factory registry: label -> callable returning a new node instance
        self._node_factories: Dict[str, Callable[[], 'QD_Node']] = {}
        self._install_default_node_factories()

    # --- Node factory management -----------------------------------------
    def _install_default_node_factories(self):
        """Register built-in primitive node types (lazy imports)."""
        self.register_node_type("Enter", self._factory_enter)
        self.register_node_type("Exit", self._factory_exit)

    def register_node_type(self, label: str, factory: Callable[[], 'QD_Node']):  # noqa: D401
        self._node_factories[label] = factory

    def node_factory_labels(self):  # noqa: D401
        return sorted(self._node_factories.keys())

    # Lazy factory wrappers (avoid import cycles during module import)
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
        # Position node centering it at click point
        try:
            br = node.boundingRect()
            node.setPos(scene_pos - br.center())
        except Exception:
            node.setPos(scene_pos)
        self.addItem(node)
        # Manage selection: clear existing & select new node
        for item in self.selectedItems():
            item.setSelected(False)
        node.setSelected(True)
        return node

    # --- Configuration API -------------------------------------------------
    def set_grid_step(self, step: int):
        self._grid_step = max(5, step)
        self.update()  # trigger redraw

    def grid_step(self) -> int:
        return self._grid_step

    # --- Drawing ------------------------------------------------------------
    def drawBackground(self, painter: QPainter, rect: QRectF):  # noqa: N802 (Qt naming)
        """Draw a lightweight infinite grid with a soft dark background.

        Major lines every 5 steps are slightly brighter for orientation.
        """
        # Background fill (do BEFORE calling base implementation)
        painter.fillRect(rect, self._BG_COLOR)

        step = self._grid_step
        if step <= 0:
            return

        # Prepare pens once
        minor_pen = QPen(self._GRID_MINOR)
        major_pen = QPen(self._GRID_MAJOR)
        for p in (minor_pen, major_pen):
            p.setWidthF(0)  # cosmetic, 1px regardless of zoom

        # Align starting coordinates to grid
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)
        right = int(rect.right())
        bottom = int(rect.bottom())

        # Vertical lines
        x = left
        top_i = int(rect.top())
        bottom_i = int(rect.bottom())
        while x <= right:
            index = int(round(x / step))
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            painter.drawLine(int(x), top_i, int(x), bottom_i)
            x += step

        # Horizontal lines
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
        """Right-click context menu to add nodes on empty space.

        Current behavior: If right-click is on empty scene area, show an 'Add Node'
        submenu listing registered node factories. Selecting one spawns the node.
        Future extensions can add node/socket specific menus.
        """
        scene_pos = event.scenePos()
        item = self.itemAt(scene_pos, QTransform())
        # Only handle empty-space menus for now
        if item is not None:
            return super().contextMenuEvent(event)

        menu = QMenu()
        add_menu = menu.addMenu("Add Node")
        for label in self.node_factory_labels():
            act = add_menu.addAction(label)
            # Capture label & position
            act.triggered.connect(lambda _checked=False, l=label, p=QPointF(scene_pos): self._spawn_node(l, p))

        menu.exec(event.screenPos())
        event.accept()

__all__ = ["QD_GfxScene"]
