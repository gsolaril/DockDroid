"""The harness: the deterministic program that owns the loop.

This file never imports a model SDK. It talks to two narrow interfaces:

    Phone   -> observe() / perform(action)      (fake now, redroid in lesson 1.x)
    Brain   -> decide(goal, observation, history, tools) -> (action, usage)

If swapping either one requires editing this file, the abstraction leaked.

Three rules encoded here, and they are the reason this file exists at all:

1. The model is never trusted. Its request is validated before execution, and
   the result of every action is re-read from the phone, not reported by the model.
2. A bad request costs one step, not the run. Tool errors become the next
   observation.
3. Every step is recorded. If it is not in the transcript, it did not happen.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from .fake_phone import ToolError

SYSTEM = """You control an Android phone through tools. You see the screen as a list of
elements, each with a stable id. Act one step at a time: choose one tool, look at
the new screen, then choose again. Never claim you did something you did not see
confirmed on screen. When the goal is reached, call done."""

# The tool surface: the only verbs the model has. Small on purpose.
# Written once, in JSON-schema form, so the same definition can later be handed
# straight to a model's tool-calling API without a rewrite.
TOOLS = [
    {
        "name": "tap",
        "description": "Press one button on the current screen. Use the element id from the observation.",
        "input_schema": {
            "type": "object",
            "properties": {"element": {"type": "string", "description": "element id, e.g. nav_jobs"}},
            "required": ["element"],
        },
    },
    {
        "name": "type_text",
        "description": "Replace the contents of one text field.",
        "input_schema": {
            "type": "object",
            "properties": {"element": {"type": "string"}, "text": {"type": "string"}},
            "required": ["element", "text"],
        },
    },
    {
        "name": "press",
        "description": "Physical key. key is 'back' or 'home'.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string", "enum": ["back", "home"]}},
            "required": ["key"],
        },
    },
    {
        "name": "scroll",
        "description": "Scroll the current list. direction is 'up' or 'down'.",
        "input_schema": {
            "type": "object",
            "properties": {"direction": {"type": "string", "enum": ["up", "down"]}},
            "required": ["direction"],
        },
    },
    {
        "name": "observe",
        "description": "Look at the screen again without acting.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "done",
        "description": "End the episode. Only call this when the screen shows the goal is reached.",
        "input_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string", "description": "one line: what is now true"}},
            "required": ["summary"],
        },
    },
]


# --------------------------------------------------------------- observation
def render(obs: dict) -> str:
    """Turn the phone's observation into the text the model reads.

    Observation design is the highest-leverage decision in an agent system
    (lesson 4). This version is deliberately naive: every element, no filtering,
    no ranking, no compression. We need a baseline before we are allowed to
    improve it.
    """
    lines = [f"SCREEN: {obs['screen']}"]
    if obs.get("toast"):
        lines.append(f"NOTE: {obs['toast']}")
    lines.append("ELEMENTS:")
    for el in obs["elements"]:
        value = f'  value="{el["value"]}"' if el.get("value") else ""
        lines.append(f'  {el["id"]:<16} {el["role"]:<7} "{el["text"]}"{value}')
    return "\n".join(lines)


def approx_tokens(text: str) -> int:
    """Cheap token estimate: ~4 characters per token for English.

    Good enough to compare two prompts. Not good enough to predict an invoice.
    We use an estimate here because lesson 0.1 must run with no API key.
    """
    return max(1, len(text) // 4)


def history_text(steps: list["Step"]) -> str:
    if not steps:
        return "(nothing yet)"
    lines = []
    for s in steps:
        action = json.dumps(s.action, ensure_ascii=False) if s.action else "{}"
        outcome = f"ERROR: {s.error}" if s.error else s.result
        lines.append(f"{s.n}. {action} -> {outcome}")
    return "\n".join(lines)


# --------------------------------------------------------------------- records
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


# ------------------------------------------------------------------ the loop
def run_episode(phone, task, brain, max_steps: int = 15) -> Episode:
    """The agent loop, and the whole of it.

    Read it once and 'agent' stops being a mystery: a for-loop, a budget, a
    validator, a recording device, and a stop condition.
    """
    phone.reset()
    ep = Episode(task_id=task.id, goal=task.goal)
    obs = phone.observe()
    t0 = time.perf_counter()

    for n in range(1, max_steps + 1):
        observation = render(obs)
        action, usage = brain.decide(
            goal=task.goal, observation=observation, history=ep.steps, tools=TOOLS
        )
        if not isinstance(action, dict) or "tool" not in action:
            action = {"tool": "__invalid__"}

        prompt_estimate = approx_tokens(
            SYSTEM + task.goal + observation + history_text(ep.steps)
        )
        completion_estimate = approx_tokens(json.dumps(action))
        prompt_tokens = usage.get("prompt_tokens") or prompt_estimate
        completion_tokens = usage.get("completion_tokens") or completion_estimate

        # ---- stop condition: the model says it is finished ----------------
        if action["tool"] == "done":
            ep.claimed_done = True
            ep.summary = str(action.get("summary", ""))
            ep.stop_reason = "done"
            ep.steps.append(
                Step(
                    n=n,
                    screen=obs["screen"],
                    action=action,
                    result="episode ended",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )
            )
            break

        # ---- execute, but never believe the outcome without looking -------
        error = None
        try:
            result = phone.perform(action)
        except ToolError as exc:
            result, error = "", str(exc)
            if action["tool"] == "__invalid__":
                error = "the request was not a valid tool call"

        obs = phone.observe()  # the screen is the truth, not the model's report
        ep.steps.append(
            Step(
                n=n,
                screen=obs["screen"],
                action=action,
                result=result,
                error=error,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )

    ep.duration_s = time.perf_counter() - t0
    return ep
