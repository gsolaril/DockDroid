"""The phone layer's contract: one error type and the two-method interface.

`ToolError` is not an exception in the "something went wrong" sense. It is the
phone saying *no*: a button that is not there, a form that cannot be submitted
empty. The harness catches it and shows it to the model as the next observation,
so a bad action costs one step instead of the run.
"""

from __future__ import annotations

from ..models.interfaces import Phone


class ToolError(Exception):
    """An action the phone refused. A normal event, not a crash."""                 


__all__ = ["Phone", "ToolError"]
