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
from PySide6.QtGui import QTransform
from PySide6.QtCore import QPointF
from qdgfxscene import QD_GfxScene

__all__ = ["QD_OpScene"]


class QD_OpScene(QD_GfxScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Install op node factory set (now includes a basic 'Op' node placeholder and 'Calc')
        self._install_default_node_factories()
        # Placeholder for op-specific initialization

    def _install_default_node_factories(self):  # noqa: D401
        """Register default operational primitives (generic Op + Calc)."""
        self.register_node_type("Calc", self._factory_calc)

    @staticmethod
    def _factory_calc():  # noqa: D401
        from nodes.op.math import Calc
        return Calc()

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
