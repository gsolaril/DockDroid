# Phone Agent — Master Course

*A project-based course in AI engineering. One project, ten modules, one measured number per increment.*

---

## 0. How this course works

**Who it is for.** A senior quant developer who is an entry-level AI engineer. You already know
engineering, statistics, latency, testing, and P&L. What you do not yet have is the intuition for
how LLM systems are built, measured, and kept cheap.

**Teaching contract.**

- Plain English first, jargon second. Every term gets its plain meaning *before* its industry name.
- Every analogy comes from trading/markets, because that is the mental model you already own.
- We never build two things at once. One concept → one small piece of code → one number.
- Every increment ends with a measurement. "It seems to work" is not a result. A rate is a result.
- If a module's concept is not needed by this project *yet*, it is named and postponed. Understanding
  what you are deliberately not learning is part of the curriculum.

**Language.** We work in English. If a concept is clearer in Spanish, ask and you get it in Spanish —
that is not a step backwards, it is removing mental calories exactly where they cost most.

**The rhythm of a session.** Each session is: (1) the idea in plain words, (2) the smallest code that
expresses it, (3) the measurement, (4) the honest result including failures, (5) homework-sized
reading or exercises. Never a 3,000-line dump.

---

## 1. The system we are building

Three layers. Only the middle one is new to you; the outer two are ordinary engineering.

```
  ┌──────────────────────────────────────────────────────────────┐
  │  THE MODEL  (Claude / GPT / Gemini — rented, not owned)      │
  │  Reads text. Writes text. Decides. Has no hands.             │
  └──────────────────────────────────────────────────────────────┘
                 ▲ state + observations      │ typed requests
                 │                           ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  THE HARNESS  (our code — deterministic Python)               │
  │  Executes requests. Records everything. Enforces limits.      │
  │  Decides when the run stops. Owns the truth of what happened. │
  └──────────────────────────────────────────────────────────────┘
                 ▲ element lists              │ taps, text, swipes
                 │                           ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  THE PHONE LAYER  (redroid in Docker + uiautomator2/adb)     │
  │  One Android instance per container, one app each.            │
  └──────────────────────────────────────────────────────────────┘
```

The single most important sentence in this course:

> **The model never touches the phone. It only ever emits requests. Our code decides whether a
> request is legal, performs it, and reports back what actually happened.**

That sentence is the difference between a demo and a system. Everything in the ten modules is a
consequence of it.

---

## 2. Glossary, in plain words

Read this once. Do not memorise it. Come back when a term bites.

### Model-side basics

- **Token** — the unit a model reads and writes. Roughly 3/4 of an English word. You are billed per
  token, in and out. Think "tick": the atomic unit that everything else is measured in.
- **Context window** — the model's working memory for one call: your instructions + the history +
  the current observation, all in tokens. Fixed size. It is a **cache of finite size**, and unlike a
  cache you cannot evict; you can only be shorter. Overflow = error.
- **Prompt** — the text you send. **System prompt** — the standing instruction block that defines
  the agent's role and rules. It is re-sent on *every call* and you pay for it every time.
- **Structured output / tool calling** — instead of asking for prose and parsing it with regexes, you
  declare a schema and the model returns JSON matching it. This is the modern replacement for "please
  answer in JSON". It is a contract, like a FIX message spec.
- **Hallucination** — the model stating something confidently that is not in its input. For us it
  means: claiming a tap succeeded, or inventing an element that is not on screen. **Never trust a
  model's claim of an action's outcome. Read it back from the phone.**
- **Fine-tuning** — further training a model on your own examples. Expensive, slow, and the wrong
  tool until you have a few hundred logged trajectories. Postponed to Module 10.

### Harness-side basics

- **Harness** — our Python code that runs the loop: build prompt → call model → parse request →
  execute on phone → capture result → repeat. It also owns logging, budgets, retries, and the stop
  condition. If the model is the trader's brain, the harness is the order gateway plus risk engine plus
  the trade blotter. **The harness is where the engineering lives, and it is 100% deterministic and
  unit-testable.**
- **Agent / agentic loop** — a program that repeatedly asks a model "what next?" and acts, until a
  stop condition. Not a magic property of the model. Just a `while` loop with a budget.
- **ReAct** — *Reason + Act*. The 2022 pattern where the model writes a short thought, then an
  action, sees the result, thinks again. Modern tool-calling loops are ReAct with a schema instead of a
  text format. You will build it in ~40 lines and it will stop being mysterious.
- **Observation** — what the harness shows the model about the current state. Ours is a numbered list
  of on-screen elements, not a screenshot. **Observation design is where most of the cost and most of
  the accuracy are decided.**
- **Grounding / verification** — checking that the action did what was intended by reading the phone
  back, instead of trusting the model. Analogous to confirming a fill against the exchange rather than
  trusting your own order state.
- **MCP (Model Context Protocol)** — an open standard for packaging "tools + resources" as a small
  server that any agent client can connect to, instead of hard-coding each tool into each app. It is
  a **plumbing convention**, like FIX or REST: it standardises how capabilities are described and
  called. Useful, not required, and definitely not a prerequisite for us. We will touch it late, once
  our own tools exist and the contrast teaches you what it buys.

### Measurement basics

- **Eval (evaluation)** — a fixed set of tasks with **automatic pass/fail checks**, run repeatedly so
  you can compare two versions of your system numerically. This is **your backtest**. Same discipline:
  fixed universe, fixed rules, no peeking, report the sample size.
- **Eval set** — the actual list of tasks. Ten tasks is a legitimate start. Fifty is better. Never
  fewer than ten, or your rates are noise.
- **Benchmark** — an eval set published by someone else so different systems can be compared. The
  famous ones here: **AndroidWorld** (116 tasks, 20 apps), **M3A** (a smaller suite), **MobileWorld**
  (201 tasks). When a paper says "62.2% cross-app" it means: of the tasks that needed two apps, 62.2%
  passed the automatic check.
- **"M3A numbers"** — the specific measured finding I quoted earlier: on M3A, giving the model an
  accessibility-tree element list scored **30.6%** and giving it a screenshot with numbered overlays
  scored **25.4%** (GPT-4 Turbo); with Gemini 1.5 Pro the ordering **flipped** (19.4% vs 22.8%). The
  lesson is not "lists are better". The lesson is: *the best observation format depends on the model,
  so you measure it on your own tasks instead of trusting a number from a paper.*
- **Cost per success** — total spend ÷ number of tasks actually completed. The only KPI that matters
  commercially. A 95% success rate at $3/task loses to 80% at $0.15/task for most real work.

### The two "RAG" words, since you asked

- **Embedding** — a vector (a list of floats, e.g. 1536 numbers) that represents the *meaning* of a
  piece of text, produced by a model. Texts with similar meaning land near each other.
- **Vector database** — a store that, given one embedding, returns the *k* stored embeddings closest
  to it, fast. That is the whole idea: nearest-neighbour search over meaning-vectors. You already know
  this mathematics (cosine distance, ANN indexes, recall/latency trade-offs); the AI industry simply
  gave it a new product category name.
- **RAG (Retrieval-Augmented Generation)** — before asking the model a question, search your own
  documents for the relevant passages (often via a vector database) and paste them into the prompt, so
  the model answers from *your* text instead of its memory. It is a **lookup-before-you-ask** pattern.

**Why RAG is not in the early modules:** our agent's "knowledge" is not documents, it is the current
screen. Retrieval would be solving a problem we do not have. When you *do* need it — remembering how
a particular job application form was filled last time — it becomes a small, obvious addition. Its
absence is a curriculum decision, not an oversight.

---

## 3. The ten modules

Each module has one question it answers, one thing you build, and one number you report.

| # | Module | The question it answers | You build | The number |
|---|--------|------------------------|-----------|------------|
| 0 | **The floor** | Can a model reliably drive a phone at all, and how would I even know? | Phone layer + harness + 10-task eval + scorer | success rate on 10 tasks, tokens/task, $/success |
| 1 | **Prompts and tokens** | What exactly am I paying for on every call? | Prompt assembly with a token budget report | tokens and $ per task, before/after |
| 2 | **Structured output** | How do I stop the model from producing unparseable text? | JSON-schema tool calls + validation + repair | malformed-output rate |
| 3 | **The loop** | What is an "agent", mechanically? | ReAct loop with step budget and stop conditions | steps/task, loop-failure rate |
| 4 | **Observation design** | What should the model see? | Compressed, indexed element lists; screenshot variants | success rate and tokens per observation variant |
| 5 | **Memory** | What must survive between steps and between runs? | Short-term history + persistent notes/store | success rate with/without, tokens saved |
| 6 | **Verification** | How do I catch "it said it was done but it wasn't"? | Read-back checks after each action, done-verifier | false-done rate, success rate |
| 7 | **Evaluation and statistics** | Is my improvement real or noise? | Repeated runs, confidence intervals, failure taxonomy | ±CI on every rate you claim |
| 8 | **Efficiency and routing** | Which model should do which step? | Cheap-model/expensive-model split, caching | $/success at fixed success rate |
| 9 | **Safety and product** | What stops this from becoming the thing that gets accounts banned? | Approval gates, rate limits, kill switch, audit log | incidents avoided, human-touch rate |
| 10 | **Fine-tuning** *(later)* | Can I make a small model do this cheaper? | Dataset from logged trajectories, tuned model | $/success vs the API |

### Why this order

- **0 before everything.** Without an eval, every later comparison is an opinion. This is the
  backtest harness. Build the ruler before the thing being measured.
- **1–2 before 3.** You cannot debug a loop whose messages you cannot read and whose output you
  cannot parse. Most beginner agent failures are prompt-format failures wearing a costume.
- **4 after 3, not before.** Observation design only makes sense once you have watched the loop
  flounder with a naive observation.
- **7 before 8.** Optimising cost before you can measure success reliably produces a cheaper system
  that does not work, and you will not be able to tell.
- **9 late but not optional.** For a phone-automation business this is the survival module.
- **10 last** because fine-tuning without a few hundred logged trajectories is guessing.

---

## 4. Module 0 in detail (the next session)

**Goal:** a phone in a container, a harness that can drive it, and a scorer that tells the truth about
how badly it drives it.

Deliverables, in build order:

1. `docker-compose.yml` + `spike.sh` — redroid 13 (x86_64, with the ARM translation layer), loopback
   only, persistent `/data`, health check that proves `adb` sees the device *and* Android finished
   booting.
2. `phone.py` — the deterministic tool layer. No LLM import anywhere in this file. Pure functions:
   `observe()`, `tap(id)`, `type_text(text)`, `scroll(dir)`, `press(key)`, `screenshot()`.
   The observation must return a numbered list of visible, interactable elements with stable ids.
3. `tasks.yaml` + `eval.py` — ten tasks with **programmatic** success checks (read state back from
   the phone; never ask the model "did you do it?"), and a scorer that prints success rate,
   mean steps, tokens, and cost per success.
4. `agent.py` — the loop. Deliberately naive in Module 0. Its job is to produce a baseline number,
   not to be good.
5. `NOTES.md` — running log: what broke, what the numbers were, what I would try next.

**Success criterion for the module is not a good success rate.** It is: *you can run one command, get
a number, change one thing, run again, and see whether the number moved.* That is the whole skill.

**Known traps, written down before we hit them:**
- redroid x86_64 images advertise `arm64-v8a` but may ship no translator → ARM-only APKs install and
  then crash on launch. Verify `getprop ro.product.cpu.abilist` and `ls /system/lib64/libnb.so`.
- `--privileged` is what redroid requires to reach the host's binder driver. It also means the
  container is **not a security boundary**. Isolation comes from the VPS, not the container.
- Touch coordinates are in the phone's pixel space, not the client's. Pin width/height/DPI in the
  container's boot args or your taps will drift silently.

---

## 5. Standing rules

1. One measured number per increment, or the increment does not count.
2. The phone layer never imports the model. The model never claims an outcome the harness has not
   read back from the phone.
3. No new dependency until the current one has been measured.
4. When the model fails, the first suspect is the observation, the second is the prompt, the third is
   the model. (In that order, always.)
5. Twenty logged failures are worth more than one clever idea. Keep the logs.
