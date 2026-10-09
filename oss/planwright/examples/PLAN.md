# Example plan

A real, small plan you can run the engine against:

```
planwright graph examples/PLAN.md
planwright next examples/PLAN.md
planwright validate examples/PLAN.md --strict
```

This is planwright's own Phase-1 build, kept as a live example. It shows two
tracks running in parallel (`engine` and `plugin`), a docs track that only the
final item depends on, and a critical path through the engine.

| ID | Title | Status | Owner | Est | Depends | Track |
|----|-------|--------|-------|-----|---------|-------|
| E1 | Data model (Item, Plan, estimates) | done | claude | 1d | - | engine |
| E2 | Markdown plan parser | done | claude | 1d | E1 | engine |
| E3 | Dependency graph (ready, layers, critical path) | done | claude | 2d | E1 | engine |
| E4 | Validator (schema, cycles, governance rule) | done | claude | 1d | E3 | engine |
| E5 | CLI (validate, graph, next, status) | done | claude | 1d | E2, E4 | engine |
| P1 | Plugin manifest + slash commands | done | claude | 0.5d | - | plugin |
| P2 | Enforcement hook (validate on edit) | done | claude | 1d | E4 | plugin |
| P3 | governed-planning skill | done | claude | 0.5d | - | plugin |
| T1 | Tests (parse, graph, validate, cli) | doing | claude | 1d | E5 | quality |
| T2 | README + POSITIONING | doing | claude | 0.5d | - | docs |
| T3 | CI workflow (ruff + tests + build) | todo | claude | 0.5d | T1 | quality |
| R1 | Release 0.1.0 | todo | maestro | 0.5d | T2, T3, P2 | release |
```
