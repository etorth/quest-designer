# -*- coding: utf-8 -*-
"""Operational graph MDI window.

QD_OpWindow specializes QD_MdiWindow for operational / logic graphs, creating
its own QD_OpScene + QD_GfxView after the refactor that moved scene/view
responsibility out of the base window class.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qdmdiwindow import QD_MdiWindow
from qdopscene import QD_OpScene
from qdgfxview import QD_GfxView

__all__ = ["QD_OpWindow"]


class QD_OpWindow(QD_MdiWindow):
    def __init__(self, title: str | None = "Op Graph", parent: QWidget | None = None, state_node=None):
        super().__init__(title=title, parent=parent)
        self._state_node = state_node  # Reference to the corresponding State node
        self._init_scene_view()

    def _init_scene_view(self):
        self.scene = QD_OpScene(self, state_node=self._state_node)
        self.view = QD_GfxView(self.scene, self)
        self.setWidget(self.view)
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def as_dict(self) -> dict:  # noqa: D401
        return {"type": self.__class__.__name__, "title": self.windowTitle()}


