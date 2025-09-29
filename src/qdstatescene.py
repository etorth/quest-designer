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
from PySide6.QtWidgets import QMenu, QMdiArea, QMdiSubWindow  # NEW import for context menu
from PySide6.QtGui import QTransform
from PySide6.QtCore import QPointF, Qt
from qdgfxscene import QD_GfxScene  # ensure base imported
from qdopwindow import QD_OpWindow  # NEW
from nodes.qdstatenode import QD_StateNode  # NEW


__all__ = ["QD_StateScene"]


class QD_StateScene(QD_GfxScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Install default state node factories (moved from base scene)
        self._install_default_node_factories()
        # Mapping: state_index -> QD_OpWindow (to avoid spawning duplicates)
        self._op_windows: dict[int, QD_OpWindow] = {}
        # Placeholder for future state-scene initialization logic
        # e.g., self._ensure_enter_node()

    def _install_default_node_factories(self):  # noqa: D401
        # Register default state primitives (Enter/Exit)
        self.register_node_type("Enter", self._factory_enter)
        self.register_node_type("Exit", self._factory_exit)

    @staticmethod
    def _factory_enter():  # noqa: D401
        from nodes.state.primitives.enter import Enter
        return Enter()

    @staticmethod
    def _factory_exit():  # noqa: D401
        from nodes.state.primitives.exit import Exit
        return Exit()

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

    # --- Node click handling to spawn Op windows -------------------------
    def mousePressEvent(self, event):  # noqa: D401
        # Only intercept left-clicks on a QD_StateNode itself (not its sockets)
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, QD_StateNode):
                self._open_op_window_for_state(item)
                # Continue to super to preserve selection behavior
        super().mousePressEvent(event)

    def _find_mdi_area(self) -> QMdiArea | None:
        # Ascend parents: scene -> QD_StateWindow (QMdiSubWindow) -> QMdiArea
        p = self.parent()
        # parent() of QGraphicsScene may not be widget; rely on provided parent (set in window init)
        if isinstance(p, QMdiSubWindow):
            mdi_parent = p.parent()
            if isinstance(mdi_parent, QMdiArea):
                return mdi_parent
        # Fallback: scan QObject chain
        while p is not None:
            if isinstance(p, QMdiArea):
                return p
            p = p.parent() if hasattr(p, 'parent') else None
        return None

    def _open_op_window_for_state(self, node: QD_StateNode):
        idx = node.state_index()
        existing = self._op_windows.get(idx)
        mdi_area = self._find_mdi_area()
        if mdi_area is None:
            return
        if existing is not None:
            try:
                if existing.isVisible():
                    existing.show()
                    existing.raise_()
                    existing.activateWindow()
                    return
            except Exception:
                pass
        # Create new op window
        title = f"OpNode_{idx}"
        op_win = QD_OpWindow(title=title)
        try:
            mdi_area.addSubWindow(op_win)
        except Exception:
            pass
        self._op_windows[idx] = op_win
        op_win.show()
        try:
            op_win.raise_()
            op_win.activateWindow()
        except Exception:
            pass
