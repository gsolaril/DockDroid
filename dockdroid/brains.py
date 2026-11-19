"""Brains: the thing that decides the next action.

Two implementations, on purpose:

    ScriptedBrain  a lookup table. No network, no randomness, no cost.
                   It is the *oracle*: if it does not score 100%, the bug is in
                   the phone, the tools or the checks -- never in a model.

    LLMBrain       the real thing: a model with tool calling. Same interface.

Having both is the lesson. When a real model scores 40% and the scripted brain
scores 100%, you know exactly where the problem is. Without the scripted brain
every failure is ambiguous.
"""

from __future__ import annotations

import json


class ScriptedBrain:
    """Replays a fixed plan. Deterministic: same input, same output, always."""

    def __init__(self, plans: dict[str, list[dict]]) -> None:
        self.plans = plans

    def decide(self, goal: str, observation: str, history: list, tools: list):
        plan = self.plans.get(goal, [])
        i = len(history)
        if i < len(plan):
            return plan[i], {}
        return {"tool": "done", "summary": "plan exhausted"}, {}


class LLMBrain:
    """A real model, with tool calling. Used from lesson 0.2 onwards.

    Status: NOT yet exercised on this machine (no API key was configured).
    Treat the first run as a debugging session, not as a result.

    Design note: this sends a fresh, self-contained message each step instead of
    replaying the provider's native tool-call transcript. That is a deliberate
    simplification for lesson 0.1 -- proper conversation state and memory are
    module 5. It costs more tokens; we will measure exactly how much.
    """

    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def decide(self, goal: str, observation: str, history: list, tools: list):
        import anthropic  # imported here so the scripted brain needs no dependency

        client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else anthropic.Anthropic()

        from .harness import SYSTEM, history_text

        user = (
            f"GOAL: {goal}\n\n"
            f"HISTORY (already done, do not repeat):\n{history_text(history)}\n\n"
            f"CURRENT SCREEN:\n{observation}\n\n"
            "Choose the single next action."
        )
        resp = client.messages.create(
            model=self.model,
            max_tokens=512,
            system=SYSTEM,
            tools=[
                {"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]}
                for t in tools
            ],
            tool_choice={"type": "any"},
            messages=[{"role": "user", "content": user}],
        )

        action: dict = {"tool": "__invalid__"}
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                action = {"tool": block.name, **block.input}
                break

        usage = {
            "prompt_tokens": resp.usage.input_tokens,
            "completion_tokens": resp.usage.output_tokens,
        }
        return action, usage
