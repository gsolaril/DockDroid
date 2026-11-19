"""The eval set: ten tasks, each with an automatic pass/fail check.

Rules that make this an eval and not a demo:

  1. The check reads the phone's state directly. It never asks the model.
  2. The goal is written in natural language, the way a user would say it.
  3. The check is written independently of the plan used to reach it.

Ten is the smallest honest number. Below that, a single task moving changes the
score by 10 points and you cannot tell a real improvement from luck.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Task:
    id: str
    goal: str
    check: Callable[[object], bool]
    max_steps: int = 15


def _has_application(phone, job: int, name: str, email: str) -> bool:
    return any(
        a["job"] == job and a["name"] == name and a["email"] == email
        for a in phone.applications
    )


TASKS: list[Task] = [
    Task(
        id="open_jobs",
        goal="Open the list of jobs.",
        check=lambda p: p.screen == "jobs",
        max_steps=5,
    ),
    Task(
        id="open_profile",
        goal="Open my profile.",
        check=lambda p: p.screen == "profile",
        max_steps=5,
    ),
    Task(
        id="set_name",
        goal="Set the Name on my profile to 'Ada Lovelace' and save it.",
        check=lambda p: p.profile["name"] == "Ada Lovelace",
        max_steps=10,
    ),
    Task(
        id="set_email",
        goal="Set the Email on my profile to 'ada@example.com' and save it.",
        check=lambda p: p.profile["email"] == "ada@example.com",
        max_steps=10,
    ),
    Task(
        id="open_job_detail",
        goal="Open the detail page of the 'Backend Engineer' job.",
        check=lambda p: p.screen == "job_detail" and p.current_job == 3,
        max_steps=10,
    ),
    Task(
        id="apply_job",
        goal=(
            "Apply to the 'Malware Analyst' job with the name 'Ada Lovelace' "
            "and the email 'ada@example.com'."
        ),
        check=lambda p: _has_application(p, 2, "Ada Lovelace", "ada@example.com"),
        max_steps=15,
    ),
    Task(
        id="jobs_then_home",
        goal="Open the list of jobs and then go back to the home screen.",
        check=lambda p: p.screen == "home",
        max_steps=10,
    ),
    Task(
        id="open_messages",
        goal="Open my messages.",
        check=lambda p: p.screen == "messages",
        max_steps=5,
    ),
    Task(
        id="open_chat",
        goal="Open the conversation with 'Team Lead - Axiom'.",
        check=lambda p: p.screen == "chat" and p.chat_open == 2,
        max_steps=10,
    ),
    # The trap. A model that taps Submit instead of Cancel still says "done",
    # and this check catches it. This is the false-done detector.
    Task(
        id="apply_then_cancel",
        goal=(
            "Open the 'Quant Developer' application form, then cancel it without "
            "applying. When you are done I want to be on the jobs list with nothing sent."
        ),
        check=lambda p: p.applications == [] and p.screen == "jobs",
        max_steps=15,
    ),
]


def by_id(task_id: str) -> Task:
    for t in TASKS:
        if t.id == task_id:
            return t
    raise SystemExit(f"unknown task {task_id!r}; available: {', '.join(t.id for t in TASKS)}")
