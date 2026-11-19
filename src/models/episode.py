"""The record of one run: the steps, and what they cost.

If it is not in here, it did not happen. That rule is why an episode is a data
structure and not a pile of print statements.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Step:
    n: int
    screen: str
    action: dict | None
    result: str
    error: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class Episode:
    task_id: str
    goal: str
    steps: list[Step] = field(default_factory=list)
    claimed_done: bool = False
    summary: str = ""
    stop_reason: str = "budget"  # done | budget
    duration_s: float = 0.0

    @property
    def tool_calls(self) -> int:
        return sum(1 for s in self.steps if s.action and s.action.get("tool") != "done")

    @property
    def errors(self) -> int:
        return sum(1 for s in self.steps if s.error)

    @property
    def prompt_tokens(self) -> int:
        return sum(s.prompt_tokens for s in self.steps)

    @property
    def completion_tokens(self) -> int:
        return sum(s.completion_tokens for s in self.steps)
