"""The phone is deterministic, so it gets ordinary unit tests.

Everything above it is only as trustworthy as this layer: if the fake phone
disagrees with reality (or with itself), every number above it is fiction.
"""

import pytest

from src.phone import FakePhone, ToolError


def tap(phone, element):
    return phone.perform({"tool": "tap", "element": element})


def test_navigation_opens_jobs():
    phone = FakePhone()
    tap(phone, "nav_jobs")
    assert phone.screen == "jobs"
    assert phone.visits == ["home", "jobs"]


def test_apply_records_an_application():
    phone = FakePhone()
    tap(phone, "nav_jobs")
    tap(phone, "job_2_apply")
    phone.perform({"tool": "type_text", "element": "form_name", "text": "Ada"})
    phone.perform({"tool": "type_text", "element": "form_email", "text": "ada@example.com"})
    tap(phone, "form_submit")
    assert phone.applications == [{"job": 2, "name": "Ada", "email": "ada@example.com"}]


def test_cancel_discards_the_draft_and_lands_on_job_detail():
    phone = FakePhone()
    tap(phone, "nav_jobs")
    tap(phone, "job_1_apply")
    tap(phone, "form_cancel")
    assert phone.applications == []
    assert phone.draft == {"name": "", "email": ""}
    assert phone.screen == "job_detail"


def test_submit_with_an_empty_field_is_refused():
    phone = FakePhone()
    tap(phone, "nav_jobs")
    tap(phone, "job_2_apply")
    with pytest.raises(ToolError):
        tap(phone, "form_submit")
    assert phone.screen == "apply_form"


def test_unknown_element_is_refused_and_state_is_unchanged():
    phone = FakePhone()
    with pytest.raises(ToolError):
        tap(phone, "nav_settings")
    assert phone.screen == "home"


def test_back_with_an_empty_stack_is_refused():
    phone = FakePhone()
    with pytest.raises(ToolError):
        phone.perform({"tool": "press", "key": "back"})


def test_unsaved_profile_change_does_not_stick():
    phone = FakePhone()
    tap(phone, "nav_profile")
    phone.perform({"tool": "type_text", "element": "p_name", "text": "Ada Lovelace"})
    tap(phone, "nav_back")
    assert phone.profile["name"] == ""
