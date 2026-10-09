#!/usr/bin/env python3
"""Scaffold an evidence-first scorecard for a candidate repository.

Implements Steps 0–1 of docs/initiatives/REPO-EVAL-PLAYBOOK.md: it writes a
scorecard skeleton (criteria + capability map + decision gate to fill by hand)
and best-effort auto-fills the objective facts (license, activity, tests, CI…)
via the `gh` CLI. If `gh` is unavailable or the repo is unreachable, the facts
are left blank with a note — the scorecard is still useful.

    python scripts/repo_scorecard.py owner/repo --job planning-kernel
    python scripts/repo_scorecard.py owner/repo --job full-autonomous-org --out docs/initiatives/evals

Standard library only. Writes to docs/initiatives/evals/<owner>__<repo>.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ["planning-kernel", "execution-runtime", "visualization", "full-autonomous-org"]

CRITERIA = [
    "Research & discovery",
    "Structural planning",
    "Executive planning",
    "Visualization",
    "Executor selection",
    "Governed execution",
    "Validation & completion",
    "Operational learning",
    "Integrity & security",
    "Portability & maintenance",
]


def _gh_json(path: str) -> dict | None:
    """Call `gh api <path>` and parse JSON; return None on any failure."""
    try:
        out = subprocess.run(
            ["gh", "api", path],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def objective_facts(owner: str, repo: str) -> dict[str, str]:
    """Best-effort objective facts; blanks (with a note) when unreachable."""
    note = "_(fetch manually — `gh` unavailable or repo unreachable)_"
    meta = _gh_json(f"repos/{owner}/{repo}")
    if meta is None:
        return {k: note for k in ("license", "pushed", "stars", "issues", "archived", "release", "lang")}
    lic = (meta.get("license") or {}).get("spdx_id") or "NOASSERTION"
    rel = _gh_json(f"repos/{owner}/{repo}/releases/latest")
    release = (rel or {}).get("tag_name", "— (no release)")
    return {
        "license": lic,
        "pushed": (meta.get("pushed_at") or "?")[:10],
        "stars": str(meta.get("stargazers_count", "?")),
        "issues": str(meta.get("open_issues_count", "?")),
        "archived": "yes ⚠️" if meta.get("archived") else "no",
        "release": release,
        "lang": meta.get("language") or "?",
    }


def render(owner: str, repo: str, job: str, facts: dict[str, str]) -> str:
    full = f"{owner}/{repo}"
    crit_rows = "\n".join(
        f"| {i} | {name} | | | not-verified | |" for i, name in enumerate(CRITERIA, 1)
    )
    map_rows = "\n".join(f"| {i} | | | not-verified | |" for i in range(1, len(CRITERIA) + 1))
    return f"""# Scorecard — {full}

> Evaluated against **{job}**. Procedure: `docs/initiatives/REPO-EVAL-PLAYBOOK.md`.
> Date: {datetime.now(timezone.utc).date().isoformat()}. Rule: evidence (file:line / test / run), not README.

## Step 0 — Job
`{job}` — compared only against this lane.

## Step 1 — Objective facts (auto)
| Fact | Value |
|------|-------|
| License (SPDX) | {facts["license"]} |
| Last push | {facts["pushed"]} |
| Latest release | {facts["release"]} |
| Open issues | {facts["issues"]} |
| Stars | {facts["stars"]} |
| Archived | {facts["archived"]} |
| Primary language | {facts["lang"]} |
| Tests present + CI | _(verify by hand: look for tests/ + .github/workflows)_ |
| Dependencies / weight | _(verify by hand)_ |
| Security (secrets, CVEs) | _(run auditron / review history)_ |

**Disqualifiers checked?** license compatible · maintained · has tests · no secrets → _(yes/no)_

## Step 2 — Capability criteria (evidence-scored)
| # | Criterion | Evidence (file:line / test / run) | Where | Status | Notes |
|---|-----------|-----------------------------------|-------|--------|-------|
{crit_rows}

Status ∈ proven / partial / absent / not-verified.

## Step 3 — Capability map (where each lives)
| # | Lives in (candidate / planwright / plan_runner / none) | Evidence | Status | Gap? |
|---|--------------------------------------------------------|----------|--------|------|
{map_rows}

## Step 4 — Canonical scenario
_(Did it run the end-to-end scenario? research → structural → executive → dispatch
with 1 HITL + budget cap → validation by evidence. Record what happened.)_

## Step 5 — Decision
- Outcome: **evolve / integrate / replace / reposition** — _(choose)_
- Evidence for the choice: _(…)_
- If integrate: which component, arm's-length or linked, license impact.

## Red flags seen
- _(…)_
"""


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Scaffold a repo evaluation scorecard.")
    ap.add_argument("repo", help="candidate repository as owner/repo")
    ap.add_argument("--job", choices=JOBS, default="full-autonomous-org", help="lane to evaluate against")
    ap.add_argument("--out", default="docs/initiatives/evals", help="output directory")
    ap.add_argument("--no-fetch", action="store_true", help="skip gh fetch (leave facts blank)")
    args = ap.parse_args(argv)

    if "/" not in args.repo:
        print("repo must be owner/repo", file=sys.stderr)
        return 2
    owner, repo = args.repo.split("/", 1)

    note = "_(not fetched)_"
    facts = (
        {k: note for k in ("license", "pushed", "stars", "issues", "archived", "release", "lang")}
        if args.no_fetch
        else objective_facts(owner, repo)
    )

    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{owner}__{repo}.md"
    out_path.write_text(render(owner, repo, args.job, facts), encoding="utf-8")
    try:
        shown = out_path.relative_to(ROOT)
    except ValueError:
        shown = out_path
    print(f"scorecard written: {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
