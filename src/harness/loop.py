"""The harness: the deterministic program that owns the loop.

This file never imports a model SDK. It talks to two narrow interfaces:

    Phone   -> observe() / perform(action)      (fake now, redroid in lesson 1.x)
    Brain   -> decide(goal, observation, history, tools) -> (action, usage)

If swapping either one requires editing this file, the abstraction leaked.

Three rules encoded here, and they are the reason this file exists at all:

1. The model is never trusted. Its request is validated before execution, and
   the result of every action is re-read from the phone, not reported by model.
2. A bad request costs one step, not the run. Tool errors become the next
   observation.
3. Every step is recorded. If it is not in the transcript, it did not happen.
"""

from __future__ import annotations

import json
import time

from ..models import Episode, Step
from ..phone.base import ToolError
from ..utils import Log
from .render import approx_tokens, history_text, render
from .tools import SYSTEM, TOOLS


def run_episode(phone, task, brain, max_steps: int = 15) -> Episode:
    """The agent loop, and the whole of it.

    Read it once and "agent" stops being a mystery: a for-loop, a budget, a
    validator, a recording device, and a stop condition.
    """
    phone.reset()
    ep = Episode(task_id=task.id, goal=task.goal)
    obs = phone.observe()
    t0 = time.perf_counter()
    Log.debug(f"episode {task.id} | goal: {task.goal} | budget {max_steps} steps")

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
            Log.debug(f"step {n} | {obs['screen']} | done -> claimed: {ep.summary!r}")
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
        outcome = f"ERROR: {error}" if error else result
        Log.debug(f"step {n} | {obs['screen']} | {action} -> {outcome}")

    ep.duration_s = time.perf_counter() - t0
    Log.debug(f"episode {task.id} finished: {len(ep.steps)} steps, {ep.duration_s:.3f}s")
    return ep
