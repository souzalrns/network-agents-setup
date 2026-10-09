# Changelog

All notable changes to planwright are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims
for [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-10-09

### Added

- **The management layer** — turns the dependency engine into something a
  manager can see and act on:
  - `planwright mermaid` — Mermaid **dependency graph** (coloured by status) and
    **Kanban board** (Ready / Doing / Blocked / Done); renders natively on
    GitHub/Markdown, zero dependencies. `--view deps|board|all`.
  - `planwright action` — a ranked action plan: what to start now ordered by
    leverage (human decisions that unblock others first, then the critical path),
    who-unblocks-what, the autonomous wave, and the critical chain.
  - Optional **Autonomy** (`auto`/`assisted`/`human`) and **Complexity**
    (`C1`..`C4`) columns, parsed when present and ignored when absent; complexity
    is cognitive risk for later cheap→expensive model routing, kept separate from
    effort (`Est`).
- 8 new tests (parsing, Mermaid, action ranking); still ruff-clean, build +
  `twine --strict` green.

## [0.1.0] — 2026-10-09

### Added

- **Plan model & parser** — read a plan from a plain Markdown table (first table
  with `ID` + `Title`); case-insensitive headers with English and Portuguese
  aliases; estimates as sizes (`S/M/L/XL`) or durations (`2h`/`3d`/`1w`).
- **Engine** — deterministic, zero-dependency: ready-now items, blocked items
  (with the ids they wait on), parallel layers (topological), critical path
  (longest chain by effort), and cycle / dangling-dependency detection.
- **Validator** — errors (parse, duplicate id, dangling/self dependency, cycle)
  and governance warnings (started without an estimate; done before its
  dependency); `--strict` promotes warnings to failures.
- **CLI** — `validate`, `graph`, `next`, `status`, each with `--json`.
- **Claude Code plugin** — `plugin.json`, slash commands (`plan-status`,
  `plan-new`, `plan-triage`), the `governed-planning` skill, and a `PostToolUse`
  hook that blocks on an unsound plan file.
- **Quality** — 35 tests (parser, graph, validator, CLI, hook), ruff clean,
  `python -m build` + `twine check` green.

[0.1.0]: https://github.com/souzalrns/network-agents-setup/tree/main/oss/planwright
