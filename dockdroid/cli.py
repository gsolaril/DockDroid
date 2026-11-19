"""Command line: the only entry point you need for now.

    python -m dockdroid                        run all ten tasks, scripted brain
    python -m dockdroid -v                     same, with full transcripts
    python -m dockdroid -t apply_job -v        one task only
    python -m dockdroid --brain llm            the real model (needs ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import argparse
import os

from .brains import LLMBrain, ScriptedBrain
from .eval import run_suite
from .plans import PLANS
from .tasks import TASKS, by_id


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dockdroid", description="Run the lesson 0.1 eval suite.")
    p.add_argument("-b", "--brain", choices=["scripted", "llm"], default="scripted")
    p.add_argument("-t", "--task", help="run a single task id")
    p.add_argument("-v", "--verbose", action="store_true", help="print every step")
    p.add_argument("-n", "--max-steps", type=int, help="override the step budget")
    p.add_argument("--model", default=os.environ.get("DOCKDROID_MODEL", "claude-sonnet-4-5"))
    args = p.parse_args(argv)

    if args.brain == "scripted":
        factory = lambda: ScriptedBrain(PLANS)
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ANTHROPIC_API_KEY is not set. Nothing to call, nothing to measure.")
            return 2
        factory = lambda: LLMBrain(model=args.model)

    tasks = [by_id(args.task)] if args.task else TASKS
    run_suite(factory, tasks=tasks, verbose=args.verbose, max_steps=args.max_steps)
    return 0
