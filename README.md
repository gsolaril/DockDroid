# DockDroid

**A deterministic harness for LLM agents that drive Android apps.**

An agent looks at a phone screen as data, decides one action at a time, and executes it through a
small, typed tool surface. The model is rented; the harness is ours. This repository is that
harness — plus the evaluation rig that keeps it honest.

> Status: **lesson 0.1**. The phone is a Python state machine, the brain is a lookup table, and the
> eval runs ten tasks locally with no API key and no containers. Real Android (redroid in Docker)
> replaces the fake phone behind the same interface in lesson 1.x.

---

## Why this exists

Most agent demos work and most agent products do not. The gap is almost never the model: it is the
unglamorous middle layer — what the model is allowed to do, what it is shown, what is verified after
each action, and what stops it. In trading terms, the model is the strategy and this repository is
the order gateway, the risk engine and the blotter. Nobody's Sharpe ratio saves them from a broken
execution stack.

So the rule the whole project is built on:

> **The model never touches the phone. It only emits requests. The harness validates them, executes
> them, and re-reads the phone to find out what actually happened.**

Everything else — the ten modules, the eval, the cost accounting — is a consequence of that rule.

---

## How it is put together

```
  model (rented)      writes one JSON action per step, sees only text
        ^
        |  observation (text)          action (validated)
        v
  harness             the loop, the tool schema, the budgets, the transcript
        ^
        |  observe()                   perform(action)
        v
  phone               fake today; redroid container tomorrow
```

| File | Role | Deterministic? |
|---|---|---|
| `dockdroid/fake_phone.py` | The phone: state machine + `observe()` / `perform()` | yes |
| `dockdroid/harness.py` | The loop, the tool schema, observation rendering, records | yes |
| `dockdroid/brains.py` | `ScriptedBrain` (oracle) and `LLMBrain` (real model) | oracle yes, model no |
| `dockdroid/tasks.py` | The eval set: 10 tasks, each with an automatic check | yes |
| `dockdroid/eval.py` | The scorer and the report | yes |
| `dockdroid/plans.py` | The oracle's shortest known trace for each task | yes |

The phone and the brain are swappable. If replacing either one requires editing `harness.py`, the
abstraction has leaked and that is a bug.

---

## Quickstart

Requires Python 3.10+. Lesson 0.1 uses only the standard library.

```bash
python -m dockdroid              # run the ten tasks, scripted brain
python -m dockdroid -v           # same, with a full step-by-step transcript
python -m dockdroid -t apply_job -v
python -m dockdroid --brain llm  # the real model; needs ANTHROPIC_API_KEY
```

## What the numbers mean

```
task               result   steps  tools  errors  tokens
apply_job          PASS         6      5       0    1384
```

- **result** — `PASS` / `FAIL` / `FALSE-DONE`. The verdict comes from the task's own check reading
  the phone's state, never from the model's claim.
- **FALSE-DONE** — the model said it finished and the check disagreed. This is the single most
  expensive failure mode in production agents, so it gets its own column.
- **steps / tools** — what the success cost in round trips.
- **tokens** — estimated as `characters / 4` while we run without an API key. Real usage numbers
  replace this the moment a model is in the loop.

---

## Baseline (lesson 0.1)

Oracle brain, ten tasks, one run:

| metric | value |
|---|---|
| success | **10/10 (100%)** |
| false-done | 0/10 |
| mean steps | 3.40 |
| mean estimated tokens | 681 |

An oracle that is correct by inspection must score 100%. The first run scored 9/10 — the failure was
a bug in the phone's back-stack, not in the plan. That is the whole method: a wrong number with a
known cause, instead of a good-looking demo with an unknown one. See `NOTES.md`.

There is no model baseline yet: no API key was configured on the development machine. That is the
next measurement, and the interesting one.

---

## Roadmap

Ten modules, one measured number each. Full syllabus in `COURSE.md`.

| # | Module | Status |
|---|---|---|
| 0 | The floor: harness, fake phone, eval set | **in progress** (0.1 done) |
| 1 | Prompts and tokens | — |
| 2 | Structured output and validation | — |
| 3 | The loop (ReAct) | — |
| 4 | Observation design and compression | — |
| 5 | Memory | — |
| 6 | Verification against false-done | — |
| 7 | Evaluation and statistics | — |
| 8 | Efficiency and model routing | — |
| 9 | Safety, limits, product | — |
| 10 | Fine-tuning (only after ~200 logged trajectories) | — |

---

## Scope and responsible use

DockDroid drives apps through their user interface, which means it is subject to those apps' terms
of service. Automating a service you do not own or have permission to automate can get accounts
restricted or banned, and several large platforms explicitly forbid it. The intended uses are your
own accounts for assistive workflows, and services that expose no API. Do not point it at other
people's accounts, and do not use it to submit things on someone else's behalf without their
approval on the final action.

Not affiliated with, endorsed by, or supported by LinkedIn or any other app vendor.

## License

Mozilla Public License 2.0 — see `LICENSE`.
