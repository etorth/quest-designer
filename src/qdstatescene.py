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

