"""A fake Android phone.

Why this file exists
--------------------
Debugging two unknowns at the same time is how projects die. In lesson 0.1 the
model is the only unknown; the phone is a deterministic state machine we can
read and reason about completely.

In lesson 1.x this class gets replaced by a real redroid container behind the
*same two methods*: `observe()` and `perform(action)`. Nothing above this file
should need to change when that happens. That is the whole point of the split.

The contract
------------
- `observe()`   -> a dict describing what is on screen right now. Read-only.
- `perform(a)`  -> executes one action, returns a short status string, or raises
                   ToolError. It never returns "success" for something it did
                   not do; the caller re-reads the screen to find out what
                   actually happened.
"""

from __future__ import annotations

from typing import Any


class ToolError(Exception):
    """An action the phone refused. This is a normal event, not a crash.

    The harness turns it into the model's next observation, so a bad action
    costs one step instead of the whole run.
    """


# The "app" behind the fake phone: a tiny job board.
JOBS = [
    (1, "Quant Developer", "Axiom Capital"),
    (2, "Malware Analyst", "Northbridge Security"),
    (3, "Backend Engineer", "Helios Data"),
    (4, "Data Engineer", "Copperline"),
    (5, "Solutions Architect", "Vantage"),
]

CHATS = [
    (1, "Recruiter - Globex"),
    (2, "Team Lead - Axiom"),
    (3, "No-reply - JobBoard"),
]


def _btn(element_id: str, text: str) -> dict:
    return {"id": element_id, "role": "button", "text": text}


def _txt(element_id: str, text: str) -> dict:
    return {"id": element_id, "role": "text", "text": text}


def _inp(element_id: str, label: str, value: str) -> dict:
    return {"id": element_id, "role": "input", "text": label, "value": value}


class FakePhone:
    def __init__(self) -> None:
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self) -> None:
        self.screen = "home"
        self.stack: list[str] = []
        self.current_job: int | None = None
        self.form_job: int | None = None
        self.profile = {"name": "", "email": ""}
        self.draft = {"name": "", "email": ""}  # what is typed but not saved yet
        self.applications: list[dict] = []
        self.chat_open: int | None = None
        self.toast = ""

    # -------------------------------------------------------------- observing
    def elements(self) -> list[dict]:
        s = self.screen
        if s == "home":
            return [
                _txt("home_title", "JobBoard"),
                _btn("nav_jobs", "Jobs"),
                _btn("nav_profile", "Profile"),
                _btn("nav_messages", "Messages"),
            ]
        if s == "jobs":
            out = [_txt("jobs_title", "Open positions")]
            for job_id, title, company in JOBS:
                out.append(_txt(f"job_{job_id}_title", f"{title} - {company}"))
                out.append(_btn(f"job_{job_id}_open", "Open"))
                out.append(_btn(f"job_{job_id}_apply", "Easy Apply"))
            out.append(_btn("nav_back", "Back"))
            return out
        if s == "job_detail":
            job_id, title, company = self._job(self.current_job)
            return [
                _txt("detail_title", title),
                _txt("detail_company", company),
                _btn("job_apply", "Easy Apply"),
                _btn("nav_back", "Back"),
            ]
        if s == "apply_form":
            return [
                _txt("form_title", "Apply"),
                _inp("form_name", "Name", self.draft["name"]),
                _inp("form_email", "Email", self.draft["email"]),
                _btn("form_submit", "Submit application"),
                _btn("form_cancel", "Cancel"),
            ]
        if s == "applied":
            return [
                _txt("applied_ok", "Application sent"),
                _btn("applied_close", "Close"),
            ]
        if s == "profile":
            return [
                _txt("profile_title", "My profile"),
                _inp("p_name", "Name", self.draft["name"]),
                _inp("p_email", "Email", self.draft["email"]),
                _btn("p_save", "Save"),
                _btn("nav_back", "Back"),
            ]
        if s == "messages":
            out = [_txt("messages_title", "Messages")]
            for chat_id, name in CHATS:
                out.append(_btn(f"chat_{chat_id}", name))
            out.append(_btn("nav_back", "Back"))
            return out
        if s == "chat":
            chat_id, name = CHATS[self.chat_open - 1]
            return [
                _txt("chat_title", name),
                _txt("chat_body", "Last message: thanks, will revert tomorrow."),
                _btn("chat_back", "Back"),
            ]
        raise ToolError(f"unknown screen {s!r}")

    def observe(self) -> dict[str, Any]:
        return {
            "screen": self.screen,
            "toast": self.toast,
            "elements": self.elements(),
        }

    # --------------------------------------------------------------- acting
    def perform(self, action: dict) -> str:
        """Execute exactly one action. Raise ToolError if it is not possible."""
        self.toast = ""
        tool = action.get("tool")
        if tool == "observe":
            return "looked again"
        if tool == "tap":
            return self._tap(str(action.get("element", "")))
        if tool == "type_text":
            return self._type(str(action.get("element", "")), str(action.get("text", "")))
        if tool == "press":
            return self._press(str(action.get("key", "")))
        if tool == "scroll":
            return "no more content"
        raise ToolError(f"unknown tool {tool!r}")

    # -------------------------------------------------------------- internals
    def _goto(self, screen: str) -> None:
        self.stack.append(self.screen)
        self.screen = screen

    def _job(self, job_id: int | None) -> tuple[int, str, str]:
        for jid, title, company in JOBS:
            if jid == job_id:
                return jid, title, company
        raise ToolError("no job is selected")

    def _find(self, element_id: str) -> dict:
        for el in self.elements():
            if el["id"] == element_id:
                return el
        raise ToolError(f"element {element_id!r} is not on this screen")

    def _tap(self, element_id: str) -> str:
        el = self._find(element_id)
        if el["role"] != "button":
            raise ToolError(f"element {element_id!r} is not tappable")

        if element_id.startswith("job_") and element_id.endswith("_open"):
            self.current_job = int(element_id.split("_")[1])
            self._goto("job_detail")
            return "opened job"
        if element_id.startswith("job_") and element_id.endswith("_apply"):
            # Easy Apply from the list behaves like the real app: it passes
            # through the detail page, so cancelling the form lands there.
            self.current_job = int(element_id.split("_")[1])
            self.form_job = self.current_job
            self.stack.append(self.screen)
            self.stack.append("job_detail")
            self.screen = "apply_form"
            return "opened application form"
        if element_id.startswith("chat_"):
            self.chat_open = int(element_id.split("_")[1])
            self._goto("chat")
            return "opened conversation"

        simple = {
            "nav_jobs": lambda: self._goto("jobs"),
            "nav_messages": lambda: self._goto("messages"),
            "nav_profile": self._open_profile,
            "nav_back": self._back,
            "chat_back": self._back,
            "job_apply": self._open_form,
            "form_cancel": self._cancel_form,
            "form_submit": self._submit_form,
            "applied_close": self._close_confirmation,
            "p_save": self._save_profile,
        }
        handler = simple.get(element_id)
        if handler is None:
            raise ToolError(f"element {element_id!r} does nothing")
        handler()
        return "ok"

    def _open_profile(self) -> None:
        self.draft = dict(self.profile)  # edit a copy, not the saved values
        self._goto("profile")

    def _open_form(self) -> None:
        if self.current_job is None:
            raise ToolError("no job is selected")
        self.form_job = self.current_job
        self._goto("apply_form")

    def _cancel_form(self) -> None:
        # Cancelling dismisses the form; it does not navigate deeper.
        self.draft = {"name": "", "email": ""}
        self.toast = "application discarded"
        self._back()

    def _close_confirmation(self) -> None:
        self.stack = ["home"]
        self.screen = "jobs"

    def _submit_form(self) -> None:
        if not self.draft["name"] or not self.draft["email"]:
            # Deliberately strict: a form with an empty field cannot be sent.
            raise ToolError("both Name and Email are required before submitting")
        self.applications.append(
            {"job": self.form_job, "name": self.draft["name"], "email": self.draft["email"]}
        )
        self._goto("applied")
        self.toast = "1 application submitted"

    def _save_profile(self) -> None:
        self.profile = dict(self.draft)
        self.toast = "profile saved"

    def _type(self, element_id: str, text: str) -> str:
        el = self._find(element_id)
        if el["role"] != "input":
            raise ToolError(f"element {element_id!r} is not a text field")
        if element_id in ("form_name", "p_name"):
            self.draft["name"] = text
        elif element_id in ("form_email", "p_email"):
            self.draft["email"] = text
        else:
            raise ToolError(f"element {element_id!r} cannot be typed into")
        return f"typed {len(text)} characters"

    def _press(self, key: str) -> str:
        if key == "back":
            self._back()
            return "went back"
        if key == "home":
            self.stack.clear()
            self.screen = "home"
            return "went home"
        raise ToolError(f"unknown key {key!r}")

    def _back(self) -> None:
        if not self.stack:
            raise ToolError("nothing to go back to")
        self.screen = self.stack.pop()
