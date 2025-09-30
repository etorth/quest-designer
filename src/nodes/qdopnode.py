# -*- coding: utf-8 -*-
"""Operation node base class.

QD_OpNode represents a generic operational node (e.g., computation, branching,
logic) in the quest graph. It currently adds no behavior beyond QD_Node but
serves as a semantic subtype for future operation-specific features such as:
- Automatic socket layout for arithmetic / logic operations
- Validation of input/output arity
- Execution or simulation hooks
"""

from qdnode import QD_Node  # TOP-LEVEL import
from qdnodesocket import SocketDirection, SocketType  # TOP-LEVEL import

__all__ = ["QD_OpNode"]


class QD_OpNode(QD_Node):
    def __init__(self, title: str = "Op", **kwargs):
        super().__init__(title=title, **kwargs)

    # Default operation node sockets are numeric (DECIMAL); subclasses may override
    def default_socket_type(self, direction: SocketDirection):  # noqa: D401
        return SocketType.DECIMAL

    def as_dict(self) -> dict:  # noqa: D401
        return {"type": self.__class__.__name__, "title": self.title()}
