# DockDroid

**A deterministic harness for LLM agents that drive Android apps.**

An agent looks at a phone screen as data, decides one action at a time, and
executes it through a small, typed tool surface. The model is rented; the harness
is ours. This repository is that harness, plus the evaluation rig that keeps it
honest.

> Status: **0.1**. The phone is a Python state machine, so the entire loop runs
> offline: ten tasks, no API key, no containers. The Docker/redroid phone plugs
> in behind the same two methods without the loop noticing.

---

## Why this exists

Most agent demos work and most agent products do not. The gap is almost never
the model: it is the unglamorous middle layer — what the model is allowed to do,
what it is shown, what is verified after each action, and what stops it. In
trading terms, the model is the strategy and this repository is the order
gateway, the risk engine and the blotter. Nobody's Sharpe ratio saves them from
a broken execution stack.

So the rule the whole project is built on:

> **The model never touches the phone. It only emits requests. The harness
> validates them, executes them, and re-reads the phone to find out what
> actually happened.**

Everything else — the tool schema, the budgets, the scorer — is a consequence
of that rule.

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

The layout mirrors the author's other Python projects: an importable `src/`
package, a `tests/` folder beside it, and `log/` for the file sink.

```
src/
  main.py                 the CLI (`python -m src`)
  models/                 Task, Step, Episode, Result, Phone/Brain protocols
  phone/                  base.py (contract + ToolError), fake.py (state machine)
  harness/                tools.py (schema), render.py (observation), loop.py,
                          scorer.py
  brains/                 scripted.py (oracle), broken.py (injection profiles),
                          llm.py (real model)
  tasks/                  demo.py (the ten tasks), plans.py (reference traces)
  utils/                  base.py (Config), logger.py (loguru sinks)
tests/                    phone, brains and scorer tests (pytest)
log/                      one file per day; gitignored, created at runtime
```

| Path | Role | Deterministic? |
|---|---|---|
| `src/phone/fake.py` | The phone: state machine + `observe()` / `perform()` | yes |
| `src/harness/loop.py` | The loop, the budgets, the transcript | yes |
| `src/harness/tools.py` | The tool schema and the system prompt | yes |
| `src/harness/scorer.py` | The scorer and the report | yes |
| `src/brains/scripted.py` | `ScriptedBrain`: the oracle | yes |
| `src/brains/broken.py` | `BrokenBrain`: fault injection profiles | yes |
| `src/brains/llm.py` | `LLMBrain`: the real model | no |
| `src/tasks/demo.py` | The eval set: 10 tasks, each with an automatic check | yes |
| `src/tasks/plans.py` | The shortest known trace for each task | yes |

The phone and the brain are swappable. If replacing either one requires editing
`src/harness/loop.py`, the abstraction has leaked and that is a bug.

---

## Quickstart

Requires Python 3.10+ and `loguru` (`pip install -e .`, or `pip install loguru`
to run in place).

```bash
python -m src                        # ten tasks, scripted brain
python -m src -v                     # same, with the DEBUG log and transcripts
python -m src -t apply_job -v
python -m src --brain broken         # the four fault-injection profiles
python -m src --brain broken -m rush
python -m src --brain llm            # the real model; needs ANTHROPIC_API_KEY
python -m pytest -q                  # the rig tests itself
```

Logs go to stdout at `INFO` (`DEBUG` with `-v`) and to `log/YYYYMMDD.log` at
`DEBUG`, always.

## What the numbers mean

```
task               result       steps  tools  errors  tokens
apply_job          PASS             6      5       0    1384
apply_then_cancel  FALSE-DONE       5      4       2    1183
```

- **result** — `PASS` / `FAIL` / `FALSE-DONE`. The verdict comes from the task's
  own check reading the phone's state, never from the model's claim.
- **FALSE-DONE** — the agent said it finished and the check disagreed. This is
  the most expensive failure mode in production agents, so it gets its own
  column.
- **steps / tools** — what the success cost in round trips.
- **errors** — actions the phone refused. A bad action costs one step, never the
  run.
- **tokens** — estimated as `characters / 4` while running without an API key.
  Provider-reported usage replaces this as soon as a model is in the loop.

---

## Reference measurements

Scripted oracle, ten tasks, one run:

| metric | value |
|---|---|
| success | **10/10 (100%)** |
| false-done | 0/10 |
| mean steps | 3.40 |
| mean estimated tokens | 681 |

### Fault injection

A scorer that only ever agrees with a correct plan is a cheerleader. Each
profile below is the reference plan with exactly one thing broken, so the only
difference between two runs is the failure we want to catch. They run in tests
and from the CLI, and they are how the rig proves that a red verdict means
something.

| brain | success | false-done | tool errors | mean steps | what it exercises |
|---|---|---|---|---|---|
| `scripted` | 10/10 | 0 | 0 | 3.40 | nothing is broken |
| `rush` | 0/10 | **10** | 0 | 1.00 | a claim with no work behind it |
| `skip` | 7/10 | 3 | 1 | 3.00 | three tasks needing a field, and they lie |
| `wrong` | 7/10 | 3 | 2 | 3.40 | submit-instead-of-cancel, with its end screen |
| `ghost` | 0/10 | 0 | 24 | 9.50 | nonexistent elements, refused but never fatal |

The `rush` profile already earned its keep: `jobs_then_home` used to check only
that the agent ended on `home`, which is where it starts, so doing nothing
passed. The check now requires the phone to have actually entered `jobs`.

No real-model baseline exists yet: no API key is configured on the development
machine. That is the next measurement.

---

## Roadmap

| Milestone | Scope | Status |
|---|---|---|
| 0.1 harness | loop, tool schema, fake phone, eval set, fault injection | done |
| 0.2 model baseline | first real-model run, provider token accounting | next |
| 0.3 native transcripts | provider tool-call history instead of re-sent text | planned |
| 1.0 container phone | redroid in Docker behind the `Phone` protocol | planned |
| 1.1 device bridge | uiautomator2 / adb implementation of the same protocol | planned |
| 1.2 observation v2 | screen compression and element ranking | planned |
| 1.3 memory | conversation state and cross-step carry-over | planned |
| 1.4 verification | claim-vs-state checks beyond the task list | planned |
| 1.5 routing | cheaper models for cheap steps, measured | planned |

---

## Scope and responsible use

DockDroid drives apps through their user interface, which means it is subject to
those apps' terms of service. Automating a service you do not own or have
permission to automate can get accounts restricted or banned, and several large
platforms explicitly forbid it. The intended uses are your own accounts for
assistive workflows, and services that expose no API. Do not point it at other
people's accounts, and do not use it to submit things on someone else's behalf
without their approval on the final action.

Not affiliated with, endorsed by, or supported by LinkedIn or any other app
vendor.

## License

Mozilla Public License 2.0 — see `LICENSE`.
