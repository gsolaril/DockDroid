"""The brains: plan coverage, and proof that each broken mode breaks one thing."""

import pytest

from src.brains import BROKEN_MODES, BrokenBrain, ScriptedBrain
from src.tasks import PLANS, TASKS

BY_GOAL = {t.goal: t for t in TASKS}


def test_every_task_has_exactly_one_plan():
    # The plans are keyed by the goal string, so a typo in either file silently
    # turns a task into "no plan" and the oracle would look broken.
    assert set(PLANS) == set(BY_GOAL)


@pytest.mark.parametrize("mode", BROKEN_MODES)
def test_broken_brains_are_deterministic(mode):
    brain = BrokenBrain(PLANS, mode=mode)
    goal = TASKS[0].goal
    first = brain.decide(goal, "", [], [])
    second = brain.decide(goal, "", [], [])
    assert first == second


@pytest.mark.parametrize("mode", BROKEN_MODES)
def test_broken_plans_never_leave_the_tool_surface(mode):
    keys = {"tool", "element", "text", "key", "direction", "summary"}
    for goal in PLANS:
        for action in BrokenBrain(PLANS, mode=mode).plan_for(goal):
            assert set(action) <= keys


def test_rush_never_touches_the_phone():
    assert [a["tool"] for a in BrokenBrain(PLANS, "rush").plan_for(TASKS[0].goal)] == ["done"]


def test_skip_drops_only_text():
    actions = BrokenBrain(PLANS, "skip").plan_for(
        "Apply to the 'Malware Analyst' job with the name 'Ada Lovelace' "
        "and the email 'ada@example.com'."
    )
    assert [a["tool"] for a in actions] == ["tap", "tap", "tap", "done"]


def test_wrong_substitutes_submit_for_cancel():
    actions = BrokenBrain(PLANS, "wrong").plan_for(
        "Open the 'Quant Developer' application form, then cancel it without "
        "applying. When you are done I want to be on the jobs list with nothing sent."
    )
    assert {"tool": "tap", "element": "form_submit"} in actions


def test_ghost_invents_ids_that_are_not_on_screen():
    actions = BrokenBrain(PLANS, "ghost").plan_for("Open the list of jobs.")
    assert actions[0]["element"] != "nav_jobs"


def test_scripted_brain_reports_done_after_the_plan():
    brain = ScriptedBrain(PLANS)
    goal = "Open the list of jobs."
    assert brain.decide(goal, "", [], [])[0] == {"tool": "tap", "element": "nav_jobs"}
    assert brain.decide(goal, "", [object()], [])[0]["tool"] == "done"
