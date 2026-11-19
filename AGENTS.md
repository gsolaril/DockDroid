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
| How to write and format code here | this file, §Code conventions |
| Why the project exists | `README.md` |

Do not duplicate the README's design rationale here, and do not restate these
conventions inside `tools.py`. One copy of each rule, in its proper home.

---

## Code conventions

Formatting is not taste here. §0 of the LTX systems manual ("STRICT personal
coding style") is the **primordial rule**, and this section is that rule carried
into Python: the spacing, the overlines, the banners, the vertical rhythm. Where
§0 is C++-specific — Allman-versus-K&R braces, `int64_t`, include layout — it does
not apply to this tree. Everything about the *look* of the code does.

### Spaces — always, everywhere

Exactly one space on each side of `=`, `==`, `!=`, `<`, `>`, `<=`, `>=` and `:=`.
No exceptions for brevity, and no tightening tokens together.

This covers assignments, default arguments, keyword arguments, conditions, and
any SQL you write by hand.

```python
# WRONG
def function(n=3): ...
if n!=3 and p>2: ...
df = DataFrame(array, columns=["A","B"])
mydict = {"A":1,"B":2}

# RIGHT
def function(n = 3): ...
if (n != 3) and (p > 2): ...
df = DataFrame(array, columns = ["A", "B"])
mydict = {"A": 1, "B": 2}
```

Always one space **after** a comma or a colon: between arguments, between
container elements, between a key and its value, after an annotation's colon.

### Conditions in parentheses

Every `if`, `elif` and `while` condition gets its operands bracketed, and each
comparison stands alone:

```python
# WRONG
if n != 3 and p > 2:

# RIGHT
if (n != 3) and (p > 2):
if (item is None) or (len(items) == 0):
while (attempts < max_attempts):
```

Negation brackets its operand too: `if not (response.ok):`.

### Docstrings — modules, classes, dataclasses, functions

Everything public carries a docstring: the module, every class, every dataclass,
every function and method. A class docstring goes on the line after the `class`
line, indented into the body — an empty class body with a docstring is a valid
body, which is exactly why dataclasses should have one.

```python
#▄▄▄▄▄▄▄▄▄▄
class Step:
    """
    One action taken, and what the phone said afterwards.
    """
    n: int
    screen: str
```

Content follows the Inputs / Outputs / intent template: what goes in, what comes
out, why the thing exists. One bullet per item. Do not restate the signature in
prose, and do not leave a docstring that only repeats the class name.

### Overlines above every class and function

Every `class` and every `def` gets a `#▄▄▄…` overline immediately above the
signature. It starts above the first character of the signature, and its length
matches the signature span up to — but not including — the colon that ends it.
So the count of `▄` equals `len(signature_without_final_colon)`.

#▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
def apply(self, action: dict, goal: str = "") -> str:

#▄▄▄▄▄▄▄▄▄▄
class Step:

Signatures that wrap over several lines get the overline sized to the first line,
as above. Exact width is a visual match, not a byte-exact requirement, but it
should not be off by more than a character or two.

### Section banners between unrelated blocks

When two neighbouring blocks handle different concerns — end of a class and start
of the next, file regions, separate subsystems in one module — separate them with
the 96-character banner pair, `#` plus 95 fill characters:

#███████████████████████████████████████████████████████████████████████████████████████████████
#▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

Use them sparingly enough that they still mean something: a banner around every
function is noise, a banner between `ToolError` and the next class is a signpost.

### Vertical rhythm

- A blank line between the end of one function or class and the next.
- Inside a function that grows past roughly 15–25 lines, insert blank lines
  between logical sections: setup, loop, verification, teardown. One continuous
  mass of statements is the failure mode this rule exists to prevent.

### Columns

- **84 columns** for added content. Exempt: Markdown, `.txt`, YAML/ENV/INI.
- `ruff` is configured at `line-length = 100`. That is a ceiling, not a target:
  the 84-column convention is stricter. Wrap the line; never raise the limit.
- `ruff`'s `E251` and `E252` are disabled in `pyproject.toml`, because the house
  spacing rule deliberately writes `n = 3` in defaults and `key = value` in
  keyword arguments, which PEP 8 would flag. Do not re-enable them, and do not
  "fix" the spaces to satisfy a linter.

### Comments

Only for fundamental lines — why a non-obvious decision was made. 1 to 3 lines,
never wider than 84 columns. A comment that narrates what the next line does is
deleted, not shortened.

### Layout, mirrors, and new packages

The tree mirrors the LTX logical layout rather than a flat dump: `src/models/`,
`src/utils/`, `src/harness/`, `src/phone/`, `src/brains/`, `src/tasks/`. A new
top-level package under `src/` appears only for a real subsystem, not for one
module that could live where it belongs.

### Truth about the tree at 0.1

The existing sources predate this section: spacing is mostly PEP 8, overlines and
banners are not drawn yet. Do not read that as permission to skip them, and do not
read this section as permission to reformat the whole tree in one commit. New code
follows these rules; files get reformatted when they are being changed for a real
reason. A mass reformat happens only when it is explicitly asked for.

---

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
