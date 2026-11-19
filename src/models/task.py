"""A task: one goal in plain English plus one independent way to check it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Task:
    id: str
    goal: str
    check: Callable[[object], bool]
    max_steps: int = 15
