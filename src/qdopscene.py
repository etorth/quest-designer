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
        # Install op node factory set (Calc, Level, CheckItem, Logic, Compare, Function, Selector, Wait)
        self._install_default_node_factories()

    def _install_default_node_factories(self):  # noqa: D401
        """Register default operational primitives."""
        self.register_node_type("等级", self._factory_level)
        self.register_node_type("等级值", self._factory_getlevel)
        self.register_node_type("物品", self._factory_checkitem)
        self.register_node_type("物品数量", self._factory_getitem)
        self.register_node_type("输入", self._factory_input)  # NEW Input node
        self.register_node_type("四则运算", self._factory_calc)
        self.register_node_type("关系运算", self._factory_compare)
        self.register_node_type("逻辑运算", self._factory_logic)
        self.register_node_type("函数", self._factory_function)
        self.register_node_type("分支", self._factory_selector)
        self.register_node_type("等待", self._factory_wait)
        self.register_node_type("入口", self._factory_enter)

    @staticmethod
    def _factory_calc():  # noqa: D401
        from nodes.op.math import Calc
        return Calc()

    @staticmethod
    def _factory_level():  # noqa: D401
        from nodes.op.game import CheckLeve
        return CheckLeve()

    @staticmethod
    def _factory_getlevel():  # noqa: D401 NEW factory
        from nodes.op.game import GetLevel
        return GetLevel()

    @staticmethod
    def _factory_checkitem():  # noqa: D401 (renamed from _factory_hasitem)
        from nodes.op.game import CheckItem
        return CheckItem()

    @staticmethod
    def _factory_logic():  # noqa: D401
        from nodes.op.math import Logic
        return Logic()

    @staticmethod
    def _factory_compare():  # noqa: D401
        from nodes.op.math import Compare
        return Compare()

    @staticmethod
    def _factory_function():  # noqa: D401 NEW factory
        from nodes.op.math import Function
        return Function()

    @staticmethod
    def _factory_selector():  # noqa: D401 NEW factory
        from nodes.op.selector import Selector
        return Selector()

    @staticmethod
    def _factory_wait():  # noqa: D401 NEW factory
        from nodes.op.wait import Wait  # updated path
        return Wait()

    @staticmethod
    def _factory_enter():  # noqa: D401 NEW factory
        from nodes.op.enter import Enter
        return Enter()

    @staticmethod
    def _factory_getitem():  # noqa: D401 NEW factory
        from nodes.op.game import GetItem
        return GetItem()

    @staticmethod
    def _factory_input():  # noqa: D401 NEW factory
        from nodes.op import Input
        return Input()

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
        add_menu = menu.addMenu("添加节点")
        for label in self.node_factory_labels():
            act = add_menu.addAction(label)
            act.triggered.connect(lambda _c=False, l=label, p=QPointF(scene_pos): self._spawn_node(l, p))
        menu.exec(event.screenPos())
        event.accept()
