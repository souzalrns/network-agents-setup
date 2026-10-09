# Repo evaluation playbook — "would an agent choose this?"

A standard, repeatable procedure to decide, **with evidence**, whether a
candidate repository is the recommended choice for a given job — and whether to
**evolve** what we have, **integrate** parts of a candidate, **replace** it, or
**reposition** it. The whole point: turn the decision from "whose README is more
convincing" into "whose code, tests and runs prove the capability."

> **Prime directive.** A README is a claim, not proof. Score a capability only
> with a pointer to evidence: `file:line`, a test, a real run, or an explicit
> **not-verified**. No evidence → the capability is *absent* for scoring.

Use `scripts/repo_scorecard.py <owner/repo> --job <kind>` to scaffold a scorecard
(objective facts auto-filled where reachable) under `docs/initiatives/evals/`.

---

## Step 0 — Classify the job (compare like with like)

Never score a candidate against the wrong category. First name the layer:

| Job | What it must do | Our incumbent |
|-----|-----------------|---------------|
| `planning-kernel` | plan as data, deps, ready/parallel/critical, validation | **planwright** |
| `execution-runtime` | authorize, dispatch, run, retry, approve, record cost | **plan_runner** |
| `visualization` | show graph/board/timeline/real state without a CLI | planwright (static) + ? |
| `full-autonomous-org` | the whole cycle 01–07 end to end | **none proven** (compose) |

A candidate is judged **only** against the job it claims. "Paperclip-style org
control" is not comparable to "planwright planning kernel"; pick the lane first.

---

## Step 1 — Objective facts (cheap, scriptable)

Gathered by the script (or by hand). These gate everything else — a beautiful
repo that is unmaintained or GPL-incompatible can be disqualified before Step 2.

| Fact | Why it matters | Red flag |
|------|----------------|----------|
| **License (SPDX)** | can we adopt/integrate at all? | GPL/AGPL into our MIT core; "no license" |
| **Last push / release cadence** | is it alive? | > 6–12 months stale; no releases |
| **Maintenance** | issues/PRs, responsiveness | pile of unanswered issues; 1-commit history |
| **Tests present + CI** | is behaviour proven? | no tests; no CI; green badge but empty suite |
| **Dependencies** | weight, lock-in, supply chain | heavy/abandoned deps; unpinned; native blobs |
| **Security hygiene** | secrets, deps audit | secrets in history; known CVEs (run auditron) |
| **Footprint** | can we read all of it? | huge codebase for a small claim |

---

## Step 2 — The 10 capability criteria (evidence-scored)

Score each **Proven / Partial / Absent / Not-verified**, each with its evidence
pointer. (Criteria from the GPT/Grok audit; they evaluate the *complete cycle*,
not a single package.)

| # | Criterion | Must demonstrate |
|---|-----------|------------------|
| 1 | **Research & discovery** | takes a goal, finds the unknowns, researches sources, reports evidence/alternatives/uncertainty |
| 2 | **Structural planning** | goal → architecture, deliverables, phases, deps, risks, acceptance, open decisions |
| 3 | **Executive planning** | structure → atomic tasks with effort, duration, resources, budget, autonomy, block conditions |
| 4 | **Visualization** | graph, Kanban, timeline, critical path, blockers, exec state — not CLI-only |
| 5 | **Executor selection** | picks agent/tool/model by task, permissions, availability, budget |
| 6 | **Governed execution** | authz, concurrency, retries, pauses, human approvals, cancel, recovery |
| 7 | **Validation & completion** | confirms acceptance with **evidence**, not "the agent said done" |
| 8 | **Operational learning** | records estimated vs actual, failures, quality, cost to improve future plans |
| 9 | **Integrity & security** | auditable history, access control, data isolation, resource limits, explicit policy |
| 10 | **Portability & maintenance** | documented contracts, tests, versions, migrations, license, multi-provider/runtime |

**Rule:** a criterion does **not** have to live inside the candidate. Map it to a
component (candidate / planwright / plan_runner / gap). We are scoring the *system*.

---

## Step 3 — Capability map (where each thing lives)

For each criterion, fill one row. This is what prevents duplicating the runner.

| Criterion | Lives in | Evidence (`file:line` / test / run) | Status | Gap? |
|-----------|----------|-------------------------------------|--------|------|
| 1 … 10 | planwright \| plan_runner \| candidate \| none | … | proven/partial/absent/not-verified | … |

If a capability already exists in `plan_runner` (HITL, budgets, events, tools),
the candidate's version of it is **not** a reason to adopt — it is a reason to
**not** duplicate.

---

## Step 4 — The canonical scenario (prove the cycle, don't describe it)

One real scenario from our ecosystem, run against the incumbent **and** (as far
as the repos allow) each serious candidate. It must force the whole loop:

> A real goal that needs: research → a structural plan → an executive plan with
> **dependencies**, **one human decision (HITL)** and a **budget cap** →
> dispatch → validation by **evidence** (not self-declaration).

Measure, for each system:
- plan correct and complete?
- deps/blockers computed correctly?
- can a manager see the next step without reading code?
- execution respects policy and does not duplicate work?
- results validated with evidence?
- cost/failures/waits observable?
- resumable after an interruption?

A candidate that cannot be driven through this scenario — regardless of its
README — has not earned the recommendation.

---

## Step 5 — Decision gate (four legitimate outcomes)

Choose the one the **evidence** supports, not the one we already started:

- **Evolve** — incumbent's architecture fits; gaps are small and well-bounded.
- **Integrate** — adopt a candidate's component where it cuts work without hurting
  security, portability or simplicity (prefer arm's-length, like auditron's engines).
- **Replace** — a candidate satisfies the requirements better and its integration
  cost is lower than continuing to build.
- **Reposition** — keep the incumbent but narrow its claim (e.g. "planwright =
  planning kernel only; never claims execution").

**Final criterion:** recommend the solution that best completes the cycle
(discover → plan → execute → validate → learn), not the prettiest README.

---

## Red flags that end an evaluation early

- README describes capabilities the code/tests do not back up.
- A second **executor**, **ledger**, or **authz** source (we already have one).
- License incompatibility (GPL/AGPL linked into MIT core).
- Stale/abandoned, or a one-commit "project."
- "Production-grade" as a self-claim with no tests, recovery, or limits.
- Autonomy/permissions presented in the UI but not **enforced** at runtime.

---

## How to run it

```bash
# 1. scaffold a scorecard (auto-fills objective facts where reachable)
python scripts/repo_scorecard.py paperclipai/paperclip --job full-autonomous-org

# 2. fill Steps 2–3 with evidence pointers (code/tests/runs), not README claims
# 3. run the canonical scenario (Step 4) against it and the incumbent
# 4. record the Step-5 decision with its evidence
```

Each completed scorecard lands in `docs/initiatives/evals/<repo>.md` and is the
auditable record behind the decision.
