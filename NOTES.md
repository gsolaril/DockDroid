# NOTES — running log

One entry per session. What broke, what the numbers were, what to try next. This file is the
project's memory and, later, its training data.

---

## 2026-11-19 — Lesson 0.1: the loop, the fake phone, the first number

**Built.** `FakePhone` (a job-board app as a state machine), the harness loop, the tool schema
(six verbs), two brains (`ScriptedBrain`, `LLMBrain`), ten tasks with automatic checks, and a scorer.

**Ran.** Oracle brain, ten tasks:

```
success rate     10/10  =  100%
claimed done     10/10
false-done       0/10
mean steps       3.40
mean tokens      681   (estimated: characters / 4)
```

**What went wrong first, and why it matters.** The first run scored **9/10** and flagged
`apply_then_cancel` as FALSE-DONE. The plan for that task was correct by inspection, so the fault had
to be in the phone. It was: `Cancel` on the application form pushed a *new* screen onto the back stack
instead of dismissing the form, so the next `Back` landed back inside the form and the agent ended on
the wrong screen while honestly reporting success.

The fix was three lines in `fake_phone.py`: cancelling is a dismissal (`_back()`), and Easy Apply from
the jobs list now passes through the detail page the way the real app does.

Two things worth keeping:

1. **A wrong 9/10 with a known cause is worth more than a good-looking 10/10 with an unknown one.**
   The oracle exists precisely to make this failure unambiguous.
2. The harness reported FALSE-DONE, not FAIL. The agent claimed success and was wrong. If we had
   trusted the model's claim, this bug would have shipped silently — and it is exactly the bug class
   that module 6 is about.

**Not measured yet.** No model baseline: no `ANTHROPIC_API_KEY` on this machine and the `anthropic`
SDK is not installed. `LLMBrain` is written but **unexercised** — treat its first run as a debugging
session, not as a result.

**Cost accounting.** Tokens are estimated as `characters / 4`. That is fine for comparing two prompts
and useless for predicting an invoice. It gets replaced with real `usage` numbers in lesson 0.2.

**Next.**

1. Install `anthropic`, set the key, run `python -m dockdroid --brain llm`. That is the first real
   baseline: success rate, steps, tokens, and above all the false-done count.
2. Record the failure taxonomy of that run before changing anything. Twenty logged failures beat one
   clever idea.
3. Compare against the oracle's mean of 3.40 steps to see where the steps are wasted.
