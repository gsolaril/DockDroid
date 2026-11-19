"""One scored episode: the run, the verdict, and the screen it ended on."""

from __future__ import annotations

from dataclasses import dataclass

from .episode import Episode
from .task import Task


@dataclass
class Result:
    task: Task
    episode: Episode
    passed: bool
    final_screen: str

    @property
    def false_done(self) -> bool:
        """The agent said it finished and the check disagreed.

        The most expensive failure mode in production agents, which is why it is
        a first-class field and not a line in a log.
        """
        return self.episode.claimed_done and not self.passed
