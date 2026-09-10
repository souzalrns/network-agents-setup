# Initiatives Backlog

> **This is a backlog of initiatives, not a roadmap.**
> Only items marked `building` are actually being developed.
> Everything else is preserved here to avoid losing long-term thinking
> while the current focus stays on the `plan_runner`.
>
> Last updated: 2026-09-10

## Status legend

- `backlog`  — registered, not yet analysed
- `research` — being investigated for viability
- `candidate`— analysed, promising
- `building` — under active development
- `parked`   — intentionally set aside

---

## Platform / Engine

| ID | Initiative | One-liner | Status |
|---|---|---|---|
| INIT-001 | plan_runner | YAML plan engine with HITL, crash recovery, external workers | building |
| INIT-002 | CI + Codecov | 51 tests, 83% coverage, automated release | building |
| INIT-003 | Fast-Path vs Full Cycle | Objective rule: 1 capability (fast) vs 2+ (full) | backlog |
| INIT-004 | Execution log with 5 metrics | % fast-path, cost/demand, reuse rate, etc. | backlog |
| INIT-005 | Capability catalog (8 fields) | id, name, description, triggers, owner, cost, status, body | backlog |
| INIT-006 | Minimal learning loop | Draft -> human review -> active | backlog |
| INIT-007 | Progressive disclosure | Metadata always visible, body only when selected | backlog |

## Memory / Knowledge (LightRAG + Cognee)

| ID | Initiative | One-liner | Status |
|---|---|---|---|
| INIT-010 | LightRAG integration | Knowledge graph per client/agent | research |
| INIT-011 | Cognee integration | Episodic memory (what worked / failed) | research |
| INIT-012 | `--client-id` + `--memory` flags | Per-client isolation via `get_sessionized_cognee_tools` | candidate |
| INIT-013 | Evidence engine | Collect, measure, compare, assign confidence — without deciding | backlog |
| INIT-014 | Cognitive data maturity | Original data unchanged, cognitive value evolves | backlog |

## Horizontals (shared capabilities)

| ID | Initiative | One-liner | Status |
|---|---|---|---|
| INIT-020 | Marketing skill | SEO, GEO, AEO, LLMO, content | building |
| INIT-021 | Code reviewer | Generic code review | backlog |
| INIT-022 | Data quality | Schema validation, Postgres performance | backlog |
| INIT-023 | TDD guide | Generic TDD | backlog |
| INIT-024 | Design system | Transversal visual direction | backlog |
| INIT-025 | Generic accounting | Version without personal PT/BR context | backlog |
| INIT-026 | Technical engineering | Civil, electrical, hydraulic, HVAC — generic version | backlog |

## Verticals (domain-specific)

| ID | Initiative | One-liner | Status |
|---|---|---|---|
| INIT-040 | Cognitive Financial Coach | No typing: photo of receipt -> extracted data | backlog |
| INIT-041 | Elderly monitoring (Wi-Fi CSI) | Fall / inactivity detection without cameras | backlog |
| INIT-042 | HVAC + Mollier | Thermodynamic analysis + diagnosis + AI | backlog |
| INIT-043 | Construction management with drones | Planned vs executed comparison (RVE) | backlog |
| INIT-044 | Insurance claims inspection | Drone -> 3D mapping -> report + evidence | backlog |
| INIT-045 | Public sector / condominium management | Request + GPS + budget + automatic tender | backlog |
| INIT-046 | Life coach | Orchestrator for finances, health, work, studies | backlog |
| INIT-047 | Legal case management | Tracking + AI + deadlines | backlog |
| INIT-048 | Construction: plan reading + inspection | Read BIM/schedule + verify reality | backlog |

## Discovery / Evolution (radars)

| ID | Initiative | One-liner | Status |
|---|---|---|---|
| INIT-060 | GitHub radar | Scan repos with X+ stars for reuse | backlog |
| INIT-061 | Scientific radar | Relevant papers for the domain | backlog |
| INIT-062 | Market radar | Trends, regulation, opportunities | backlog |
| INIT-063 | Opportunity Discovery Engine | Suggest businesses from existing capabilities | backlog |
| INIT-064 | Repo maturity index | Activity, contributors, tests, license — not just stars | backlog |

## Economics / Cost

| ID | Initiative | One-liner | Status |
|---|---|---|---|
| INIT-080 | Token economy | Cognitive budget per demand | backlog |
| INIT-081 | Capability ROI | Measure value generated vs maintenance cost | backlog |
| INIT-082 | Build vs Integrate vs Buy | Lifecycle-based decision, not price | backlog |
| INIT-083 | Technology quarantine | Proposal -> analysis -> test -> benchmark -> approval | backlog |

## Conceptual architecture (reference only)

| ID | Initiative | One-liner | Status |
|---|---|---|---|
| INIT-100 | PCU Constitution | Principles document (draft in docs/drafts/) | parked |
| INIT-101 | META Compiler / MCL | DSL that generates code from specification | parked |
| INIT-102 | AR-000 to AR-015 | Bounded contexts, DDD, entities — formalism | parked |

> **Note on `parked`**: it does not mean "bad idea". It means "not the current focus".
> These documents remain in `docs/drafts/` for future reference.

---

## How to use this file

- **Add new initiative**: new row in the correct category
- **Change status**: edit the status column
- **Promote to project**: move to `docs/roadmap.md`
- **Park**: change status, keep the row (history matters)

**Rule**: no initiative is ever deleted. Only its status changes.
