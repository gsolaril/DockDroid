"""Command line: the only entry point you need.

    python -m src                              all ten tasks, scripted brain
    python -m src -v                           same, with the step log and transcripts
    python -m src -t apply_job -v              one task only
    python -m src --brain broken               all four deliberately-broken brains
    python -m src --brain broken --mode rush   one of them
    python -m src --brain llm                  the real model (needs ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import argparse
import os

from .brains import BROKEN_MODES, BrokenBrain, LLMBrain, ScriptedBrain
from .harness import run_suite
from .tasks import PLANS, TASKS, by_id
from .utils import Log, configure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dockdroid", description="DockDroid eval harness.")
    parser.add_argument(
        "-b", "--brain", choices=["scripted", "broken", "llm"], default="scripted",
        help="who decides the next action (default: scripted oracle)",
    )
    parser.add_argument(
        "-m", "--mode", choices=list(BROKEN_MODES),
        help="which broken brain to run (default: all four)",
    )
    parser.add_argument("-t", "--task", help="run a single task id")
    parser.add_argument("-v", "--verbose", action="store_true", help="DEBUG log + transcripts")
    parser.add_argument("-n", "--max-steps", type=int, help="override the step budget")
    parser.add_argument("--model", default=os.environ.get("DOCKDROID_MODEL", "claude-sonnet-4-5"))
    args = parser.parse_args(argv)

    if args.mode and args.brain != "broken":
        parser.error("--mode only applies to --brain broken")

    if args.verbose:
        configure("DEBUG")

    if args.brain == "scripted":
        suites = [("scripted (oracle)", lambda: ScriptedBrain(PLANS))]
    elif args.brain == "broken":
        modes = [args.mode] if args.mode else list(BROKEN_MODES)
        suites = [(f"broken ({m})", lambda m=m: BrokenBrain(PLANS, mode=m)) for m in modes]
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            Log.error("ANTHROPIC_API_KEY is not set. Nothing to call, nothing to measure.")
            return 2
        suites = [("llm", lambda: LLMBrain(model=args.model))]

    tasks = [by_id(args.task)] if args.task else TASKS
    for title, factory in suites:
        Log.info(f"brain: {title}")
        run_suite(factory, tasks=tasks, verbose=args.verbose, max_steps=args.max_steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
