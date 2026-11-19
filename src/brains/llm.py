"""A real model, with tool calling. Same interface as the other two brains.

Status: NOT yet exercised on this machine (no API key was configured). Treat the
first run as a debugging session, not as a result.

Design note: this sends a fresh, self-contained message each step instead of
replaying the provider's native tool-call transcript. That is a deliberate
simplification for lesson 0.1 -- proper conversation state and memory are module
5. It costs more tokens; we will measure exactly how much.
"""

from __future__ import annotations

from ..harness.render import history_text
from ..harness.tools import SYSTEM
from ..utils import Log


class LLMBrain:
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def decide(self, goal: str, observation: str, history: list, tools: list):
        import anthropic  # imported here so the scripted brain needs no dependency

        client = (
            anthropic.Anthropic(api_key=self.api_key)
            if self.api_key
            else anthropic.Anthropic()
        )

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
        Log.debug(f"[llm] {action} ({usage['prompt_tokens']}+{usage['completion_tokens']} tokens)")
        return action, usage
