# -*- coding: utf-8 -*-
"""Operational graph specialized graphics scene.

QD_OpScene extends QD_GfxScene for graphs centered on operational / logic
nodes (e.g., condition checks, branching logic, scripted actions). Right now
it simply inherits behavior, serving as a semantic anchor for future features:

Potential future extensions:
- Automatic socket layout helpers for common op node types
- Inline evaluation / simulation overlays
- Grouping or compartmentalization (e.g., collapsible logic blocks)
- Validation passes (unused outputs, unreachable ops)
"""
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QTransform, QColor
from PySide6.QtCore import QPointF
from qdgfxscene import QD_GfxScene

__all__ = ["QD_OpScene"]


class QD_OpScene(QD_GfxScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply op-specific palette (cool blue tint)
        self.set_palette(
            QColor(0x26, 0x31, 0x3d),  # background
            QColor(0x33, 0x3f, 0x4c),  # minor grid
            QColor(0x44, 0x55, 0x66),  # major grid
        )
        # Install op node factory set (now includes a basic 'Calc' + 'Level' + 'HasItem' + 'Logic' + 'Compare')
        self._install_default_node_factories()
        # Placeholder for op-specific initialization

    def _install_default_node_factories(self):  # noqa: D401
        """Register default operational primitives (Calc + Level + HasItem + Logic + Compare)."""
        self.register_node_type("Calc", self._factory_calc)
        self.register_node_type("Level", self._factory_level)
        self.register_node_type("HasItem", self._factory_hasitem)
        self.register_node_type("Logic", self._factory_logic)
        self.register_node_type("Compare", self._factory_compare)  # NEW

    @staticmethod
    def _factory_calc():  # noqa: D401
        from nodes.op.math import Calc
        return Calc()

    @staticmethod
    def _factory_level():  # noqa: D401
        from nodes.op.game import Level
        return Level()

    @staticmethod
    def _factory_hasitem():  # noqa: D401 NEW factory
        from nodes.op.game import HasItem
        return HasItem()

    @staticmethod
    def _factory_logic():  # noqa: D401 NEW factory
        from nodes.op.math import Logic
        return Logic()

    @staticmethod
    def _factory_compare():  # noqa: D401 NEW factory
        from nodes.op.math import Compare
        return Compare()

    # Example future hook
    def analyze(self):  # noqa: D401
        """Perform a placeholder analysis (to be implemented)."""
        pass

    def contextMenuEvent(self, event):  # noqa: D401
        scene_pos = event.scenePos()
        item = self.itemAt(scene_pos, QTransform())
        if item is not None:
            return super().contextMenuEvent(event)
        menu = QMenu()
        add_menu = menu.addMenu("Add Op Node")
        for label in self.node_factory_labels():
            act = add_menu.addAction(label)
            act.triggered.connect(lambda _c=False, l=label, p=QPointF(scene_pos): self._spawn_node(l, p))
        menu.exec(event.screenPos())
        event.accept()
