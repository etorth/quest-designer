# -*- coding: utf-8 -*-
"""MDI subwindow base for QuestDesigner.

After refactor, this base no longer instantiates a scene/view. Subclasses
(e.g. QD_StateWindow) are responsible for creating and assigning
`self.scene` (a QGraphicsScene subclass) and `self.view` (a QD_GfxView).
"""
from PySide6.QtWidgets import QMdiSubWindow, QGraphicsView
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from qdgfxscene import QD_GfxScene  # noqa: F401
    from qdgfxview import QD_GfxView  # noqa: F401


class QD_MdiWindow(QMdiSubWindow):
    def __init__(self, title: str | None = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        if title:
            self.setWindowTitle(title)
        # NOTE: subclasses must define: self.scene, self.view

    # --- Zoom convenience (delegates to subclass-provided view) ---
    def zoom_in(self):  # noqa: D401
        self.view.zoom_in()  # type: ignore[attr-defined]

    def zoom_out(self):  # noqa: D401
        self.view.zoom_out()  # type: ignore[attr-defined]

    def reset_zoom(self):  # noqa: D401
        self.view.reset_zoom()  # type: ignore[attr-defined]

    def fit_scene(self):  # noqa: D401
        self.view.fit_scene()  # type: ignore[attr-defined]

    def current_zoom_percent(self) -> int:  # noqa: D401
        scale = self.view.transform().m11()  # type: ignore[attr-defined]
        return int(round(scale * 100))

    # Public accessors (optional convenience)
    def graphics_scene(self):  # noqa: D401
        return getattr(self, "scene", None)

    def graphics_view(self) -> 'QD_GfxView | None':  # noqa: D401
        from typing import cast
        return cast('QD_GfxView | None', getattr(self, "view", None))

__all__ = ["QD_MdiWindow"]
