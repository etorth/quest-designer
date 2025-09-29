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
    def __init__(self, title: str = "State", **kwargs):
        super().__init__(title=title, **kwargs)

    def as_dict(self) -> dict:  # noqa: D401
        return {"type": self.__class__.__name__, "title": self.title()}

