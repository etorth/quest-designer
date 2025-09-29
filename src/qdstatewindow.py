# -*- coding: utf-8 -*-
"""State graph MDI window.

QD_StateWindow is a specialization of QD_MdiWindow that now owns creation of
its scene (QD_StateScene) and view (QD_GfxView) after refactor removing that
logic from the base class.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qdmdiwindow import QD_MdiWindow
from qdstatescene import QD_StateScene
from qdgfxview import QD_GfxView

__all__ = ["QD_StateWindow"]


class QD_StateWindow(QD_MdiWindow):
    def __init__(self, title: str | None = "State Graph", parent: QWidget | None = None):
        super().__init__(title=title, parent=parent)
        self._init_scene_view()

    def _init_scene_view(self):
        # Create specialized state scene and attach to custom zoomable view
        self.scene = QD_StateScene(self)
        self.view = QD_GfxView(self.scene, self)
        # Optional: tweak view parameters specifically for state graphs here later
        self.setWidget(self.view)
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # Example placeholder for future extension
    def as_dict(self) -> dict:  # noqa: D401
        return {"type": self.__class__.__name__, "title": self.windowTitle()}
