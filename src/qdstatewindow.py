# -*- coding: utf-8 -*-
"""State graph MDI window.

QD_StateWindow is a semantic specialization of QD_MdiWindow intended for
editing state (quest) graphs. It currently adds only a clearer default title
and a few placeholder hooks for future state-specific UI (toolbars, validation
panels, etc.).
"""

from qdmdiwindow import QD_MdiWindow

__all__ = ["QD_StateWindow"]


class QD_StateWindow(QD_MdiWindow):
    def __init__(self, title: str | None = "State Graph", parent=None):
        super().__init__(title=title, parent=parent)
        # Future: self._install_state_toolbar(); self._attach_validation_layer()

    # Example placeholder for future extension
    def as_dict(self) -> dict:  # noqa: D401
        """Return minimal metadata representation (extend later)."""
        return {"type": self.__class__.__name__, "title": self.windowTitle()}

