# -*- coding: utf-8 -*-
"""State node base class.

QD_StateNode adds a semantic layer above QD_Node for nodes that represent
quest/state-machine states. Future extensions may include:
- Validation rules (e.g., constraints on incoming/outgoing edges)
- Serialization helpers for exporting a state graph
- Common styling overrides specific to state nodes
"""

from qdnode import QD_Node

__all__ = ["QD_StateNode"]


class QD_StateNode(QD_Node):
    # Class-level monotonically increasing counter for unique per-instance index
    _COUNTER = 0

    def __init__(self, title: str = "State", **kwargs):
        self._state_index = QD_StateNode._COUNTER
        QD_StateNode._COUNTER += 1
        super().__init__(title=title, **kwargs)

    def state_index(self) -> int:  # noqa: D401
        """Return the unique creation index of this state node (starting at 0)."""
        return self._state_index

    # Backwards-compatible alias
    def index(self) -> int:  # noqa: D401
        return self._state_index

    def as_dict(self) -> dict:  # noqa: D401
        base = {"type": self.__class__.__name__, "title": self.title()}
        base["index"] = self._state_index
        return base
