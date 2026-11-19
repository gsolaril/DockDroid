"""The oracle: a lookup table that replays a fixed plan.

Deterministic: same input, same output, always. No network, no randomness, no
cost. If this brain does not score 100%, the bug is in the phone, the tools or
the checks -- never in a model.

That is the whole reason it exists. When a real model scores 40% and this scores
100%, you know exactly where the problem is. Without it, every failure is
ambiguous.
"""

from __future__ import annotations

from ..utils import Log


class ScriptedBrain:
    def __init__(self, plans: dict[str, list[dict]]) -> None:
        self.plans = plans

    def decide(self, goal: str, observation: str, history: list, tools: list):
        plan = self.plans.get(goal, [])
        i = len(history)
        action = plan[i] if i < len(plan) else {"tool": "done", "summary": "plan exhausted"}
        Log.debug(f"[scripted] step {i + 1}/{len(plan)}: {action}")
        return action, {}
