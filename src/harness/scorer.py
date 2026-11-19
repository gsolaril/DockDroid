"""The scorer. This is our backtest.

It runs every task, applies the task's independent check, and prints numbers.
Nothing here knows how the agent works, which is why it can be trusted to
compare two agents.

The headline numbers, in the order that matters:

  success          of the tasks, how many actually passed the check
  false_done       tasks where the model said 'done' and was wrong
  steps / tokens   what success cost
"""

from __future__ import annotations

from ..models import Result, Task
from ..phone.fake import FakePhone
from ..utils import Log
from .loop import run_episode
from ..tasks import TASKS


def run_task(task: Task, brain_factory, verbose: bool = False, max_steps: int | None = None) -> Result:
    phone = FakePhone()
    brain = brain_factory()
    ep = run_episode(phone, task, brain, max_steps=max_steps or task.max_steps)
    passed = bool(task.check(phone))
    result = Result(task=task, episode=ep, passed=passed, final_screen=phone.screen)
    if verbose:
        print_transcript(result)
    return result


def print_transcript(result: Result) -> None:
    ep = result.episode
    print(f"\n=== {ep.task_id} ===")
    print(f"GOAL: {ep.goal}")
    for s in ep.steps:
        action = s.action.get("tool") if s.action else "?"
        detail = ", ".join(
            f"{k}={v!r}" for k, v in (s.action or {}).items() if k in ("element", "text", "key")
        )
        outcome = f"ERROR: {s.error}" if s.error else s.result
        print(f"  {s.n:>2}. [{s.screen}] {action}({detail}) -> {outcome}")
    verdict = "PASS" if result.passed else "FAIL"
    claim = "claimed done" if ep.claimed_done else f"stopped: {ep.stop_reason}"
    print(f"  => {verdict} ({claim}), final screen: {result.final_screen}")


def run_suite(brain_factory, tasks: list[Task] | None = None, verbose: bool = False,
              max_steps: int | None = None) -> list[Result]:
    tasks = tasks or TASKS
    results = [run_task(t, brain_factory, verbose=verbose, max_steps=max_steps) for t in tasks]
    report(results)
    return results


def summarise(results: list[Result]) -> str:
    """One line per brain: the only comparison that matters in lesson 0.x."""
    n = len(results)
    passed = sum(r.passed for r in results)
    false_done = sum(r.false_done for r in results)
    errors = sum(r.episode.errors for r in results)
    steps = sum(len(r.episode.steps) for r in results) / n
    return (
        f"success {passed}/{n} | false-done {false_done} | "
        f"tool errors {errors} | mean steps {steps:.2f}"
    )


def report(results: list[Result]) -> None:
    w = max(len(r.task.id) for r in results) + 2
    print()
    print(f"{'task':<{w}}{'result':<12}{'steps':>6}{'tools':>7}{'errors':>8}{'tokens':>8}")
    print("-" * (w + 41))
    for r in results:
        ep = r.episode
        verdict = "PASS" if r.passed else ("FALSE-DONE" if r.false_done else "FAIL")
        print(
            f"{r.task.id:<{w}}{verdict:<12}{len(ep.steps):>6}{ep.tool_calls:>7}"
            f"{ep.errors:>8}{ep.prompt_tokens + ep.completion_tokens:>8}"
        )
    print("-" * (w + 41))

    n = len(results)
    passed = sum(r.passed for r in results)
    false_done = sum(r.false_done for r in results)
    steps = sum(len(r.episode.steps) for r in results) / n
    tokens = sum(r.episode.prompt_tokens + r.episode.completion_tokens for r in results) / n
    claimed = sum(r.episode.claimed_done for r in results)

    print(f"success rate     {passed}/{n}  =  {passed / n:.0%}")
    print(f"claimed done     {claimed}/{n}")
    print(f"false-done       {false_done}/{n}")
    print(f"mean steps       {steps:.2f}")
    print(f"mean tokens      {tokens:.0f}   (estimated: characters / 4)")
    print()
    Log.info(summarise(results))
