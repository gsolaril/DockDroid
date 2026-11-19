"""The scorer: does the rig agree with a correct plan, and reject wrong ones?

This is the file that makes the numbers trustworthy. The oracle proves the rig
is not broken; the broken brains prove it is not a cheerleader.
"""

import pytest

from src.brains import BrokenBrain, ScriptedBrain
from src.harness import run_task
from src.tasks import PLANS, TASKS, by_id

ORACLE_STEPS = 3.40


def run_all(mode=None):
    factory = (
        (lambda: ScriptedBrain(PLANS))
        if mode is None
        else (lambda: BrokenBrain(PLANS, mode=mode))
    )
    return [run_task(task, factory) for task in TASKS]


# ------------------------------------------------------------------- the rig
def test_oracle_scores_a_hundred_percent_with_no_errors():
    results = run_all()
    assert [r.task.id for r in results if not r.passed] == []
    assert sum(r.episode.errors for r in results) == 0


def test_oracle_mean_steps_match_the_recorded_baseline():
    steps = sum(len(r.episode.steps) for r in run_all()) / len(TASKS)
    assert steps == pytest.approx(ORACLE_STEPS)


# --------------------------------------------------------- lying is detected
def test_rush_is_caught_as_false_done_on_every_task():
    results = run_all("rush")
    assert not any(r.passed for r in results)
    assert all(r.false_done for r in results)


def test_home_alone_does_not_satisfy_jobs_then_home():
    # The agent starts on home. "End on home" must not be enough: the check has
    # to prove the visit actually happened. This is the hole `rush` found.
    result = run_task(
        by_id("jobs_then_home"), lambda: BrokenBrain(PLANS, mode="rush")
    )
    assert not result.passed
    assert result.false_done


def test_skipping_the_typing_fails_exactly_the_tasks_that_need_it():
    results = run_all("skip")
    failed = {r.task.id for r in results if not r.passed}
    # `apply_then_cancel` is not in this set: opening a form and cancelling it
    # needs no typing, so skip only breaks tasks that must fill a field.
    assert failed == {"set_name", "set_email", "apply_job"}
    assert all(r.false_done for r in results if not r.passed)


def test_wrong_button_sends_the_application_we_were_asked_to_cancel():
    result = run_task(by_id("apply_then_cancel"), lambda: BrokenBrain(PLANS, mode="wrong"))
    assert not result.passed
    assert result.false_done
    # Two errors, both correct: submitting an empty form is refused, and the
    # form has no Back button, so the plan's `nav_back` is refused too. The
    # agent then claims success while sitting on the form it was told to leave.
    assert result.episode.errors == 2
    assert result.final_screen == "apply_form"


def test_wrong_button_leaves_the_profile_unsaved():
    for task_id in ("set_name", "set_email"):
        result = run_task(by_id(task_id), lambda: BrokenBrain(PLANS, mode="wrong"))
        assert not result.passed
        assert result.false_done


# ------------------------------------------------------- errors are not lies
def test_ghost_elements_are_counted_and_never_claim_success():
    results = run_all("ghost")
    assert not any(r.passed for r in results)
    assert not any(r.false_done for r in results)
    assert all(r.episode.stop_reason == "budget" for r in results)
    assert sum(r.episode.errors for r in results) > 0


def test_a_tool_error_costs_one_step_not_the_run():
    # The first ghost tap fails, the brain keeps going, and the episode still
    # ends on budget with a full transcript.
    result = run_task(by_id("open_jobs"), lambda: BrokenBrain(PLANS, mode="ghost"))
    assert result.episode.errors >= 1
    assert len(result.episode.steps) == by_id("open_jobs").max_steps
