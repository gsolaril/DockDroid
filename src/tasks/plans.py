"""The oracle's plans: what a perfect operator would do, task by task.

This is not cheating -- it is a unit test of everything except the model. If a
plan that is correct by inspection fails, the bug is ours.

It doubles as documentation: the shortest known trace for each task is a useful
benchmark for "how many steps should this cost?". The oracle's 3.40 mean steps is
the floor the model is measured against.
"""

from __future__ import annotations

PLANS: dict[str, list[dict]] = {
    "Open the list of jobs.": [
        {"tool": "tap", "element": "nav_jobs"},
        {"tool": "done", "summary": "jobs list is open"},
    ],
    "Open my profile.": [
        {"tool": "tap", "element": "nav_profile"},
        {"tool": "done", "summary": "profile is open"},
    ],
    "Set the Name on my profile to 'Ada Lovelace' and save it.": [
        {"tool": "tap", "element": "nav_profile"},
        {"tool": "type_text", "element": "p_name", "text": "Ada Lovelace"},
        {"tool": "tap", "element": "p_save"},
        {"tool": "done", "summary": "name saved as Ada Lovelace"},
    ],
    "Set the Email on my profile to 'ada@example.com' and save it.": [
        {"tool": "tap", "element": "nav_profile"},
        {"tool": "type_text", "element": "p_email", "text": "ada@example.com"},
        {"tool": "tap", "element": "p_save"},
        {"tool": "done", "summary": "email saved"},
    ],
    "Open the detail page of the 'Backend Engineer' job.": [
        {"tool": "tap", "element": "nav_jobs"},
        {"tool": "tap", "element": "job_3_open"},
        {"tool": "done", "summary": "Backend Engineer detail page is open"},
    ],
    "Apply to the 'Malware Analyst' job with the name 'Ada Lovelace' and the email 'ada@example.com'.": [
        {"tool": "tap", "element": "nav_jobs"},
        {"tool": "tap", "element": "job_2_apply"},
        {"tool": "type_text", "element": "form_name", "text": "Ada Lovelace"},
        {"tool": "type_text", "element": "form_email", "text": "ada@example.com"},
        {"tool": "tap", "element": "form_submit"},
        {"tool": "done", "summary": "application to Malware Analyst submitted"},
    ],
    "Open the list of jobs and then go back to the home screen.": [
        {"tool": "tap", "element": "nav_jobs"},
        {"tool": "press", "key": "back"},
        {"tool": "done", "summary": "back on home"},
    ],
    "Open my messages.": [
        {"tool": "tap", "element": "nav_messages"},
        {"tool": "done", "summary": "messages are open"},
    ],
    "Open the conversation with 'Team Lead - Axiom'.": [
        {"tool": "tap", "element": "nav_messages"},
        {"tool": "tap", "element": "chat_2"},
        {"tool": "done", "summary": "conversation with Team Lead - Axiom is open"},
    ],
    "Open the 'Quant Developer' application form, then cancel it without applying. When you are done I want to be on the jobs list with nothing sent.": [
        {"tool": "tap", "element": "nav_jobs"},
        {"tool": "tap", "element": "job_1_apply"},
        {"tool": "tap", "element": "form_cancel"},
        {"tool": "tap", "element": "nav_back"},
        {"tool": "done", "summary": "form cancelled, nothing sent, back on jobs list"},
    ],
}
