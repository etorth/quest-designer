# -*- coding: utf-8 -*-
"""State graph specialized graphics scene.

QD_StateScene extends QD_GfxScene with a semantic purpose: it is intended to
host state (quest) nodes specifically. For now it doesn't override behavior,
but this subclass provides a clean place to add state-specific features later:

Planned potential extensions:
- Automatic insertion of an Enter node when empty
- Validation overlays / visual cues (unreachable states, dangling edges)
- State graph export / serialization helpers
- Per-state grouping, swimlanes, or hierarchical region drawing
"""
from PySide6.QtWidgets import QMenu  # NEW import for context menu
from PySide6.QtGui import QTransform
from PySide6.QtCore import QPointF
from qdgfxscene import QD_GfxScene  # ensure base imported


__all__ = ["QD_StateScene"]


class QD_StateScene(QD_GfxScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Placeholder for future state-scene initialization logic
        # e.g., self._ensure_enter_node()

    # Example placeholder hook for future logic
    def ensure_root(self):  # noqa: D401
        """Ensure at least one 'Enter' node exists (future implementation)."""
        pass

    # Specialized context menu (moved from base). Future: customize entries.
    def contextMenuEvent(self, event):  # noqa: D401
        scene_pos = event.scenePos()
        item = self.itemAt(scene_pos, QTransform())
        if item is not None:
            return super().contextMenuEvent(event)
        menu = QMenu()
        add_menu = menu.addMenu("Add State Node")
        for label in self.node_factory_labels():
            act = add_menu.addAction(label)
            act.triggered.connect(lambda _c=False, l=label, p=QPointF(scene_pos): self._spawn_node(l, p))
        menu.exec(event.screenPos())
        event.accept()
