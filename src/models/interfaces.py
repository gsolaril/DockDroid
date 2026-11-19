"""The two seams of the whole system, written down as types.

Everything above the phone and everything below the brain depends only on these
two shapes. That is why lesson 1.x can swap `FakePhone` for a redroid container
and lesson 0.2 can swap `ScriptedBrain` for a real model without touching the
loop: the loop was never talking to a concrete class.

`Protocol` rather than an abstract base class on purpose. LTX-Python's
`BaseAgent` uses inheritance; here structural typing keeps both sides ignorant
of each other, which is what makes the fake phone a real substitute.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Phone(Protocol):
    """What the loop is allowed to assume about a phone. Two methods, no more."""

    def observe(self) -> dict[str, Any]:
        """Return the current screen as plain data. Read-only, never raises."""

    def perform(self, action: dict[str, Any]) -> str:
        """Execute one action and return a short status, or raise ToolError.

        It never reports success for something it did not do. The caller re-reads
        the screen to find out what actually happened.
        """


@runtime_checkable
class Brain(Protocol):
    """What the loop is allowed to assume about a model. One method."""

    def decide(
        self, goal: str, observation: str, history: list, tools: list
    ) -> tuple[dict[str, Any], dict[str, int]]:
        """Return (action, usage). `usage` may be empty; the harness estimates."""
