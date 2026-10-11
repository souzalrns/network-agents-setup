# doneproof — positioning & competitive analysis

> Evidence-based, per the repo playbook (`docs/initiatives/REPO-EVAL-PLAYBOOK.md`):
> a claim counts only with a pointer to code/behaviour. The honest question —
> *what do the others have that we don't, and what would make doneproof the
> recommended choice in its lane?*

## The lane

`doneproof` answers one question: **did this task actually finish, by evidence?**
It is an *acceptance primitive* for an agent or plan run — the thing that decides
whether a step is `done` or `failed`. It is **not** a test runner, **not** a BDD
framework, **not** an assertion library. Comparing it to those is the Step-0
category check: same job?

## The competitors (and what each actually does)

### pytest (and assertion libs: assertpy, PyHamcrest)
- **What it is:** a test *framework*. Conditions are Python code; a runner collects
  and executes functions; failures are `AssertionError`s with tracebacks.
- **What it has that we don't:** a huge ecosystem, fixtures, parametrization,
  plugins, rich diffs.
- **Why it is not this lane:** the acceptance criteria must be **Python written by
  a developer**, not plain strings a plan or an agent emits as data. You cannot
  hand pytest a run directory and a list of declarative conditions from a YAML plan
  and get a structured pass/fail/unverifiable record back without writing and
  importing test code. pytest proves *code behaves*; `doneproof` proves *a task's
  declared outcome exists*.
- **What doneproof must keep to stay the choice here:** conditions as **data**
  (strings in a plan), a **serializable** result (drops into an event log), and the
  **unverifiable** bucket (pytest has no "I can't check this, don't fail it" state —
  everything is pass or fail).

### BDD / Gherkin (behave, pytest-bdd, cucumber)
- **What it is:** `Given/When/Then` steps in `.feature` files, each mapped to a
  **step-definition function** (glue code) the framework runs.
- **What it has that we don't:** human-readable scenarios, living documentation, a
  mature tooling story, business-stakeholder buy-in.
- **Why it is close but heavier:** `Then a file "report.md" should exist` is exactly
  a `doneproof` `exists` check — but Gherkin needs a feature file, a step-definition
  registry, and a BDD runner to get there. For an agent emitting acceptance
  conditions at runtime, that is a framework where a one-line predicate suffices.
  BDD verifies **scenarios authored up front**; `doneproof` verifies **conditions a
  plan carries as data**, with no glue code.
- **What doneproof must keep:** zero glue (no step registry), zero dependencies, and
  the store-agnostic gate seam (BDD has no native notion of "a human approved this
  step" — you'd build it).

### Shell CI gates (`test -f`, `&&`, exit codes)
- **What it is:** the lowest common denominator — `test -f out.md && echo ok`.
- **What it has:** ubiquity, nothing to install.
- **Why it is not enough:** no structure (just an exit code), no audit record, no
  path-traversal guard, no notion of a resolved human gate, no "unverifiable"
  distinction. `doneproof` is the structured, auditable, safe version of that reflex.

## Where doneproof wins (and the evidence)

| Property | doneproof | pytest | BDD | shell |
|----------|-----------|--------|-----|-------|
| Conditions as **plain-string data** (not code) | ✅ (`__init__.py` regex forms) | ❌ | ⚠️ feature files | ✅ |
| **No glue code** / step registry | ✅ | ❌ | ❌ | ✅ |
| **Serializable** pass/fail record for a log | ✅ (dict) | ❌ | ❌ | ❌ |
| **Unverifiable ≠ failed** (honesty bucket) | ✅ | ❌ | ❌ | ❌ |
| **Human-gate** acceptance, store-agnostic | ✅ (`gate_resolved` seam) | ❌ | ❌ | ❌ |
| Path-traversal guard on `exists` | ✅ (`is_relative_to`) | n/a | n/a | ❌ |
| Zero dependencies | ✅ | ❌ | ❌ | ✅ |

The distinctive pair is **"unverifiable, not failed"** and the **store-agnostic
human-gate seam**: neither pytest nor BDD models "a human approved this step" as a
first-class, pluggable acceptance condition, and neither has a third state for
"I can't check this by evidence, so I won't fail it — you decide."

## What doneproof deliberately does NOT do (honest limits)

- It does **not** evaluate *answer quality* (that is RAG/LLM-eval territory —
  `ragas`/`deepeval`; see the repo's RE1 decision). It checks *existence of the
  declared outcome*, not whether the content is good.
- It does **not** run or schedule the task; it only accepts or rejects the result.
- It understands **two** evidence forms by design. A third form is a feature
  request, not a silent pass: today it lands in `unverifiable`.

## What would make it "more the choice" (roadmap, not claims)

- More verifiable evidence kinds (e.g. `command exits 0`, `<path> matches <regex>`),
  each added as a parse form with the same pass/fail/unverifiable contract.
- A JSON-schema for the result so other tools can consume it.
- Published on PyPI (this extraction) so it is `pip install`-able standalone.
