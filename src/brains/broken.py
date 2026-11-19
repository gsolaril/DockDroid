"""Brains that are wrong on purpose: the rig's own test.

A scorer that only ever agrees with a correct plan is not a scorer, it is a
cheerleader. These brains are the negative control. Each one is a single
deliberate mutation of the oracle plan, so the only thing that changed between
two runs is the behaviour we want to catch. If a mode below does not produce the
failure it is designed to produce, the bug is in the rig.

Four modes, four failure classes:

  rush   claims success at step 1, without doing anything. Every task must
         come back FALSE-DONE. This is the "the model says it is done" failure.
  skip   drops every text field. Navigation still works, so the easy tasks
         pass and only the tasks that need typing fail -- all of them liars.
  wrong  taps the plausible-but-wrong button: Submit where the goal says
         Cancel, Back where the goal says Save. Looks like real model output.
  ghost  taps element ids that were never on screen ("nav_settings",
         "form_send"). The phone refuses every one, so we exercise the
         ToolError path and the error column, and the run ends on the budget
         instead of a false claim.

The point of the exercise is not that the model can be wrong. It is that the
rig says *which kind* of wrong, with a number, without anyone reading the
transcript.
"""

from __future__ import annotations

from ..utils import Log

BROKEN_MODES = ("rush", "skip", "wrong", "ghost")

# Plausible ids a model would invent if it were guessing from the prompt.
GHOST = {
    "nav_jobs": "nav_settings",
    "nav_messages": "nav_inbox",
    "nav_profile": "nav_account",
    "nav_back": "nav_up",
    "job_apply": "apply_now",
    "form_submit": "form_send",
    "form_cancel": "form_discard",
    "p_save": "p_apply",
    "chat_back": "chat_close",
    "applied_close": "applied_done",
}


def _ghost(element: str) -> str:
    if element in GHOST:
        return GHOST[element]
    if element.startswith("job_") and element.endswith("_open"):
        return element.replace("_open", "_view")
    if element.startswith("job_") and element.endswith("_apply"):
        return element.replace("_apply", "_easy_apply")
    if element.startswith("chat_"):
        return element + "_open"
    return element


class BrokenBrain:
    """The oracle plan, with exactly one thing broken."""

    MODES = BROKEN_MODES

    def __init__(self, plans: dict[str, list[dict]], mode: str = "rush") -> None:
        if mode not in BROKEN_MODES:
            raise ValueError(f"unknown mode {mode!r}; choose from {BROKEN_MODES}")
        self.plans = plans
        self.mode = mode
        self._cache: dict[str, list[dict]] = {}

    # ------------------------------------------------------------- the plan
    def plan_for(self, goal: str) -> list[dict]:
        if goal not in self._cache:
            self._cache[goal] = self._mutate(self.plans.get(goal, []))
        return self._cache[goal]

    def _mutate(self, plan: list[dict]) -> list[dict]:
        if self.mode == "rush":
            # Say it is done before doing anything. One step, always.
            return [{"tool": "done", "summary": "all set, nothing left to do"}]
        if self.mode == "skip":
            # Skip every field, but keep navigating.
            return [a for a in plan if a.get("tool") != "type_text"]
        if self.mode == "wrong":
            return [self._wrong(a) for a in plan]
        # ghost: a blind agent never sees evidence, so it cannot honestly close
        # the episode. Dropping the plan's final `done` keeps this mode about
        # tool errors and budget, not about lying.
        return [self._ghostly(a) for a in plan if a.get("tool") != "done"]

    @staticmethod
    def _wrong(action: dict) -> dict:
        if action.get("tool") == "tap":
            if action["element"] == "form_cancel":
                # Submits the application the user asked us not to send.
                return {"tool": "tap", "element": "form_submit"}
            if action["element"] == "p_save":
                # Leaves the profile without saving it.
                return {"tool": "tap", "element": "nav_back"}
        return action

    @staticmethod
    def _ghostly(action: dict) -> dict:
        if action.get("tool") in ("tap", "type_text"):
            return {**action, "element": _ghost(action["element"])}
        return action

    def _exhausted(self) -> dict:
        """What the brain does when its plan runs out.

        Only `ghost` keeps going: it taps, sees nothing change and taps again.
        The other three are liars to the end.
        """
        if self.mode == "ghost":
            return {"tool": "observe"}
        return {"tool": "done", "summary": "plan exhausted"}

    # ----------------------------------------------------------- the brain
    def decide(self, goal: str, observation: str, history: list, tools: list):
        plan = self.plan_for(goal)
        i = len(history)
        action = plan[i] if i < len(plan) else self._exhausted()
        Log.debug(f"[broken:{self.mode}] step {i + 1}/{len(plan)}: {action}")
        return action, {}
