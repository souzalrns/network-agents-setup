# Capability matrix — the autonomous repos (skill-scout · auditron · rag-eval)

> Self-audit per `docs/initiatives/REPO-EVAL-PLAYBOOK.md`, evaluated at `main`
> `cd4720e`. Evidence is **code and tests only**. Companion to
> `CAPABILITY-MATRIX-PLANWRIGHT.md` (the planning-kernel question); together they
> close Fase A for all four autonomous projects.

## Method note (why not the same 10 criteria)

The 10 criteria in the playbook evaluate a **planning + autonomous-execution**
system. skill-scout, auditron and rag-eval are **not** that — they are
single-purpose tools in different categories. Scoring a security scanner against
"governed execution" or "research & discovery" would be a category error. So each
is judged against (a) **domain fit** — what makes it "the choice" in *its*
category — and (b) the **transversal autonomous-repo criteria** that apply to any
pluggable package. This is the playbook's Step 0 ("classify the job; compare like
with like") applied honestly.

Status legend: **proven** (code + passing test) · **partial** · **absent** · **N/V**.

## Summary (all four)

| Project | Category | Standalone? | Tests | CI | PyPI | Verdict |
|---------|----------|-------------|-------|----|----|---------|
| planwright | planning kernel | ✅ zero-dep | 48 | ✅ | ❌ 404 | kernel candidate (see its own matrix) |
| **skill-scout** | skill supply-chain security | ✅ (1 dep) | ~169 | ✅ `skill-scout.yml` | ❌ 404 | **strong** — Fase 1 done; gap: runtime sandbox + PyPI |
| **auditron** | defensive security gate (SCA+SAST+workflow) | ✅ (3 engine deps) | 25 | ✅ `auditron.yml` | ❌ 404 | **strong** — thin orchestrator; gap: +engines/MCP + PyPI |
| **rag-eval** | RAG/retrieval evaluation | ❌ **not extracted** | (l5_eval) | via runner CI | ❌ n/a | **candidate only** — decide go/no-go (RE1) + decouple first |

Transversal criteria (apply to all): **A** single purpose · **B** standalone &
installable · **C** low lock-in · **D** tested + CI · **E** licensed + packaged ·
**F** documented boundary · **G** autonomy test · **H** security hygiene · **I**
published (PyPI).

---

## 1. skill-scout — *vet third-party Agent Skills before an agent trusts them*

**Objective facts:** MIT; `requires-python >=3.10`; 1 runtime dep
(`agentic-skills-manager>=1.0.4`); CLI `skill-scout`; 20 modules; 8 test files
(~169 tests per #143); own CI `skill-scout.yml` (Py 3.10+3.13, real engine, build
+ `twine --strict`, SARIF to code scanning). Not on PyPI (404).

### Domain fit (would an agent choose this to vet skills?)
| # | Capability | Status | Evidence |
|---|-----------|--------|----------|
| S1 | Find candidate skills | **proven** | `find.py`, `locate.py`, `source.py` |
| S2 | Static scan → verdict + SARIF | **proven** | `engines.py`, `sarif.py` · tests |
| S3 | Human approval pinned to hash, refused to AI agents | **proven** | `approval.py`, `treehash.py`, `agents.py` |
| S4 | Pin (sha256) + lockfile + chained audit | **proven** | `lock.py`, `audit.py` |
| S5 | Lifecycle: install/update/uninstall/verify/waive | **proven** | `install.py`, `lifecycle.py`, `verify.py`, `waivers.py` |
| S6 | ~80 agent targets | **proven** | `agents.py` |
| S7 | Spec validation | **proven** | `spec.py` |
| S8 | **Runtime sandbox** of a skill's scripts (behaviour) | **absent** | SKILL-SCOUT-2 (open) — it vets *before* trust, it does not *contain at run* |

### Transversal
A ✅ · B ✅ (`pip install skill-scout`, own CLI) · C ✅ (1 permissive dep) · D ✅
· E ✅ (MIT, build+twine) · F ✅ (README + SKILL-SCOUT.md) · G ✅ **autonomy test**:
no monorepo import, works standalone · H ✅ (scannable, SARIF) · I ❌ (not on PyPI).

**Verdict:** the **strongest** standalone of the three. "Would an agent choose it?"
— **yes** for pre-trust vetting + lifecycle. Honest limit: it is a *vetter*, not a
*runtime sandbox* (S8 absent → SKILL-SCOUT-2). Next: reposition the claim to
"pre-trust + lifecycle (sandbox = Phase 2)"; publish to PyPI (SKILL-SCOUT-3).

---

## 2. auditron — *one defensive security gate: SCA + SAST + workflow*

**Objective facts:** MIT; `>=3.10`; deps = the 3 engines (`pip-audit`, `bandit`,
`zizmor`) + `tomli` (<3.11); CLI `auditron`; 7 modules; 5 test files (25 tests);
own CI `auditron.yml` (build + `twine --strict`, wheel licences, clean-venv run
produces SARIF). Not on PyPI (404).

### Domain fit (would an agent choose this as a repo's security gate?)
| # | Capability | Status | Evidence |
|---|-----------|--------|----------|
| G1 | Orchestrate pip-audit + bandit + zizmor | **proven** | `scanners.py` · tests |
| G2 | One common model + report (JSON + SARIF 2.1.0) | **proven** | `model.py`, `report.py` |
| G3 | One policy (`auditron.toml`, blocking/disabled) | **proven** | `config.py` |
| G4 | One exit code / CI gate | **proven** | `core.py`, `cli.py` · CI run |
| G5 | Pluggable into any repo unchanged | **proven** | `examples/`, `.github/workflows/auditron.yml` |
| G6 | More engines (osv-scanner/Trivy, secrets) | **absent** | AUDITRON-2 (open) |
| G7 | MCP wrapper (agents call `scan`) | **absent** | AUDITRON-2 (open) |

### Transversal
A ✅ · B ✅ · C ⚠️ (3 runtime engine deps — by design; it *orchestrates*, doesn't
reimplement) · D ✅ · E ✅ · F ✅ (README + POSITIONING "honest choice") · G ✅
**autonomy test**: no monorepo import · H ✅ (it *is* a security tool) · I ❌ (PyPI).

**Verdict:** strong standalone gate. "Would an agent choose it?" — **yes**, as a
*thin orchestrator* (its honesty is that it adds no detection of its own; it
composes mature engines — the right call, same lens we apply everywhere). Gaps are
additive (G6/G7 = AUDITRON-2) and publish (PyPI). Reposition: none needed; the
POSITIONING already states the orchestrator role.

---

## 3. rag-eval — *evaluate RAG retrieval against a golden set* (candidate, not a repo)

**Status: not extracted.** It exists as `runner/plan_runner/l5_eval.py` +
`runner/tests/test_l5_eval.py`, **inside** plan_runner.

### Domain fit (the engine, where it lives today)
| # | Capability | Status | Evidence |
|---|-----------|--------|----------|
| E1 | Golden-set eval, offline (`validate`) | **proven** | `l5_eval.py` · `test_l5_eval.py` |
| E2 | Real retrieve measurement (`run`) | **partial** | needs `MCP_URL`+`MCP_API_KEY`; coupled to `McpKnowledge` |
| E3 | Metrics: provenance_ok, source_hit@k, chunk_hit, MRR | **proven** | `l5_eval.py` · tests |
| E4 | Regression gate (R-011) | **proven** | `l5_eval.py` (gate block) · `test_l5_eval.py` |
| E5 | Pluggable backend (not tied to one MCP) | **absent** | `from .mcp_knowledge import McpKnowledge` (l5_eval.py:157) |

### Transversal
A ✅ (clear purpose) · B ❌ (not a package) · C ❌ (imports `.chunking`,
`.knowledge`, `.mcp_knowledge`) · D ✅ (tested in runner) · E — (no own pyproject)
· F ❌ · G ❌ **autonomy test fails**: cannot delete plan_runner and keep it ·
H n/a · I ❌.

**Verdict:** a **good engine, zero extraction**. It is **not** an autonomous repo
yet — the honest call is the playbook's Step 5 = **decide go/no-go first (RE1)**.
If go: extraction requires a **pluggable backend** (replace the hard
`McpKnowledge` import with an interface) so `run` is not tied to our MCP; `validate`
is already offline. Name (`rag-eval`) not yet decided. Do **not** present it as an
autonomous project until extracted.

---

## Phase-close summary (to send)

- **skill-scout:** autonomous ✅, Fase 1 proven; **evolve** (reposition claim) +
  **publish**; sandbox (SKILL-SCOUT-2) is the real feature gap.
- **auditron:** autonomous ✅, proven thin gate; **leave as-is** + **publish**;
  +engines/MCP (AUDITRON-2) are additive, not blockers.
- **rag-eval:** **not autonomous yet**; **decide (RE1)** then **extract with a
  pluggable backend** before any "repo" claim.
- Shared gap across all four: **none is on PyPI** → the XP1 extraction+publish
  playbook is the one move that lifts skill-scout, auditron and planwright at once.

**Honest overall:** three of the four are genuine standalone candidates
(planwright, skill-scout, auditron); rag-eval is a candidate *engine* awaiting a
decision and a decoupling. The evidence here is what makes that a finding, not an
opinion.
