# AGENTS.md — engineering conventions for DockDroid

## Scope: read this first

This file is addressed to the agents that *edit this repository*. It is an
engineering document. It is not part of the product, it is not a prompt, and none
of it reaches a model at runtime.

- **Applies to:** any agent, human or otherwise, writing to `src/`, `tests/`,
  configuration or documentation here.
- **Does not apply to:** the execution model. That model never loads this file;
  its entire world is assembled at runtime from `src/harness/tools.py`.
- **If you are a runtime model:** this text is not your instruction set. Your
  instructions are `SYSTEM` and `TOOLS` in `src/harness/tools.py`. Ignore
  everything below and follow those.

---

## Two AIs, one repository, no shared context

DockDroid is AI all the way down, in two distinct roles that must not leak into
each other:

| | Engineering agent | Execution model |
|---|---|---|
| Role | Teaches, designs, writes and reviews the harness | Decides one action per step at runtime |
| Reads | This file, the source tree, the README | `SYSTEM`, the tool schema, the rendered observation |
| May change | `src/`, `tests/`, docs, config | Nothing but its own emitted action |
| Rules live in | `AGENTS.md` (this file) | `src/harness/tools.py` |
| If the two get mixed | Conventions quietly become agent policy | Engineering prose leaks into the prompt |

**The rule:** engineering instructions never enter a runtime prompt, and runtime
policy never hides in documentation. Changing how the execution model behaves is
a code change in `tools.py` — reviewed like any other, not written as prose here
and hoped for.

### Where each kind of rule belongs

| Question | File |
|---|---|
| What the model is told, and what verbs it has | `src/harness/tools.py` |
| What the model is shown, and how much | `src/harness/render.py`, `src/harness/loop.py` |
| What the model may do to a phone, and what refusal looks like | `src/phone/base.py` |
| Task definitions and reference traces | `src/tasks/` |
| How a run is judged | `src/harness/scorer.py` |
| How to edit this repository | this file |
| Why the project exists | `README.md` |

Do not duplicate the README's design rationale here, and do not restate these
conventions inside `tools.py`. One copy of each rule, in its proper home.

---

## Code conventions

- **Docstrings** follow the Inputs / Outputs / intent template: what goes in,
  what comes out, and why the thing exists. One bullet per item, no paragraph
  restating the signature.
- **84 columns** for added content. Exempt: Markdown, `.txt`, YAML/ENV/INI.
- `ruff` is configured at `line-length = 100`. That is a ceiling, not a target:
  the 84-column convention is stricter. Wrap the line; never raise the limit.
- **Comments** only for fundamental lines — why a non-obvious decision was made.
  1 to 3 lines, never wider than 84 columns.
- `from __future__ import annotations` at the top of every module; type hints on
  public functions. Target is Python 3.10 and newer.
- The runtime path must stay offline: no network, no API key and no container to
  run the ten reference tasks. Anything that breaks that is a regression.

## Dependencies and modules

- `requirements.txt` is the single source of dependencies; `pyproject.toml` loads
  it dynamically. Do not add dependencies to `pyproject.toml`.
- Commented entries there are reserved for the module that will need them (the
  real phone layer, 1.x). Do not uncomment one before the code that uses it
  exists and is measured.
- A new dependency needs a demonstrated need or a measurement, not convenience.
- New code arrives with the module it belongs to. Half-built layers left in the
  tree are worse than absent ones.

## Verification

- `pytest -q` must pass. At 0.1 that is 30 tests, all offline.
- `LLMBrain` has not been exercised on a machine without an API key: treat its
  first live run as a debugging session, not as a result.
- Do not add a dev dependency, a fixture or a test framework for a one-off check.

## Never commit

`.env`, `log/`, `__pycache__/`, `.pytest_cache/`, build output, and local working
notes. `.gitignore` enforces most of it; read `git status` before `git add -A`,
because it usually is not empty when you assume it is.

## Branches and history

- `main` is the published line. Work happens on `feat/<module>-<topic>`.
- Commit subject states the change in the imperative; the body says why. Keep
  both free of course material, lesson numbering and local paths.
