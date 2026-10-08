# skill-notary

**Scan, approve, pin and audit third-party Agent Skills before your agent trusts them.**

An [Agent Skill](https://agentskills.io) is a folder (`SKILL.md`, scripts, references) that an
agent loads and follows. Installing one from GitHub gives its author a say in what your agent
reads, runs and sends. `skill-notary` puts a notary between the download and the agent:

1. **scan** with mature engines (it writes no rules of its own);
2. **block** anything high or critical; never install on an engine failure;
3. ask a **human** to approve the exact content, by its hash, and refuse when the "human" is an
   AI agent;
4. **install** exactly the approved bytes, atomically;
5. **pin** them in a lock file and record every step in a **tamper-evident audit log**;
6. **verify** later that nothing drifted.

```
skill-notary install anthropics/skills@pdf
```

> Status: 0.1.0, alpha. Incubated in
> [`souzalrns/network-agents-setup`](https://github.com/souzalrns/network-agents-setup/tree/main/oss/skill-notary);
> not yet on PyPI.

## Why another tool

| | skills CLI (`npx skills`) | agentic-skills-manager | skill-guard (PR gate) | Cisco skill-scanner | **skill-notary** |
|---|---|---|---|---|---|
| Installs from `owner/repo@skill` | yes | yes | no | no | **yes** |
| Security check before install | shows remote ratings (Gen, Socket, Snyk); does not block | yes, local static scan; blocks high/critical | n/a (gate on your own repo) | n/a (scanner only) | **yes, 1 or 2 local engines merged; blocks high/critical** |
| Human approval, never automatic | no | no (passes → installs) | n/a | n/a | **yes, bound to the content hash** |
| Refuses approval by an AI agent | no | no | n/a | n/a | **yes** |
| Approval bound to the reviewed content | no | no approval step | n/a | n/a | **yes: the hash you reviewed must match what is fetched, and each copied file is re-checked** |
| Lock file with content hash | yes (locale-dependent hash) | install metadata | no | no | **yes, deterministic** |
| Tamper-evident audit log | no | no | no | no | **yes (hash chain)** |
| Drift check of installed skills | update check | update check | no | no | **yes (`verify`)** |
| SARIF for GitHub code scanning | no | no | no (JSON, Markdown) | yes | **yes, validated against the OASIS schema** |
| No secret in reports | n/a | n/a | n/a | JSON includes matched snippets | **yes (snippets and descriptions dropped)** |

Projects compared: [vercel-labs/skills](https://github.com/vercel-labs/skills),
[agentic-skills-manager](https://github.com/mazen160/skills-manager),
[skill-guard](https://github.com/vaibhavtupe/skill-guard),
[cisco-ai-defense/skill-scanner](https://github.com/cisco-ai-defense/skill-scanner)
(state of October 2026). skill-notary uses two of them as engines.

## Install

```bash
pip install ./oss/skill-notary            # from this repository (Python 3.10+)
pip install './oss/skill-notary[cisco]'   # + the Cisco engine (about 650 MB of dependencies)
```

`git` must be on `PATH` for GitHub sources.

## Use

```bash
# 1. Look: nothing is installed. Note the content hash.
skill-notary scan anthropics/skills@pdf
skill-notary scan ./skills --format sarif -o skills.sarif     # whole folder, for code scanning

# 2. Install. In a terminal you are asked to type the first 12 characters of the hash.
skill-notary install anthropics/skills@pdf
#    Non-interactive (CI, scripts): pass the full hash you reviewed.
skill-notary install anthropics/skills@pdf --approve-sha256 <hash from step 1>

# 3. Later, and in CI: is everything still exactly what was approved?
skill-notary verify --dest .claude/skills
```

Sources: `owner/repo@skill` (the `npx skills add` syntax), `owner/repo`, `https://github.com/owner/repo`,
or a local folder (`./path`). `--ref` fetches a branch, tag or commit. Default destination:
`.claude/skills` (`--dest`). Files written next to it: `skill-notary.lock.json` and
`skill-notary.audit.jsonl` (`--lock`, `--audit`). Commit both.

## How it decides

| Verdict | When | Install |
|---|---|---|
| `safe` | only info or low findings | after human approval |
| `risky` | medium findings | after human approval, with the findings shown |
| `dangerous` | any high or critical finding, or a symlink or special file | **never** |
| `not_scanned` | an engine failed | **never** (fail-closed) |

`safe` means the static scan found nothing that blocks. It is not proof that a skill is safe.

### Engines

| `--engine` | Project | Licence | What it runs |
|---|---|---|---|
| `asm` (default) | agentic-skills-manager | MIT | static checks: secrets, pipe-to-shell, destructive commands, hooks, binaries, archives, symlinks, evasion |
| `cisco` | Cisco AI Defense skill-scanner | Apache-2.0 | YAML + YARA signatures, bytecode, pipeline, correlation and AST dataflow (behavioral); offline |

`--engine asm,cisco` runs both and merges the findings (the worst severity wins). The AI or
cloud modes of the engines (LLM review, VirusTotal, AI Defense) are never enabled: they need
API keys and send the source out. Engines run in a child process with a timeout and a minimal
environment; neither executes the skill.

### Approval

1. `dangerous` or `not_scanned`: blocked before anyone is asked.
2. If an AI coding agent is detected (Claude Code, Codex, Cursor, Gemini CLI, Copilot, OpenCode, …;
   checks ported from [`@vercel/detect-agent`](https://github.com/vercel/vercel/tree/main/packages/detect-agent)),
   approval is refused, even with the right hash. Run the install yourself.
3. `--approve-sha256 HASH` must be the full content hash of this fetch. If the source changed
   since you reviewed it, the hashes differ and nothing is installed.
4. Otherwise, in an interactive terminal, you type the first 12 characters of the hash.
5. Otherwise: refused. There is no `--yes`.

The install then writes only the files of the pinned manifest, checks each file's sha256 while
writing, re-hashes the staged copy and renames it into place. Modes become 0644 or 0755; setuid
and group-write bits are dropped.

### Content hash (`skill-notary-tree-v1`)

sha256 over one JSON line `[path, executable, sha256]` per regular file, sorted by code point
(the `skills` CLI sorts with `localeCompare`, so its hash depends on the machine's locale).
Symlinks and special files are not hashed and make the skill `dangerous`.

### Lock file and audit log

The lock file records, per skill: source, commit, skill path, content hash, verdict, engines and
versions, approval (mode, actor, time) and the audit record of the install. The audit log is
JSON Lines; each record carries the hash of the previous one, so an edit, deletion or reordering
breaks the chain. `verify` checks the chain, re-hashes every installed skill, matches each lock
entry with its `installed` audit record (catching a hand-edited lock or a cut log) and, with
`--dest`, lists skill folders that are not in the lock.

## GitHub code scanning

```yaml
permissions:
  contents: read
  security-events: write
steps:
  - uses: actions/checkout@<sha>
  - run: pip install ./oss/skill-notary
  - run: skill-notary scan ./skills --format sarif -o skills.sarif --fail-on none
  - uses: github/codeql-action/upload-sarif@<sha>
    with: { sarif_file: skills.sarif, category: skill-notary }
```

Rules carry `security-severity` (critical 9.5, high 8.0, medium 5.5, low 3.0), results carry
stable `partialFingerprints` and paths relative to the repository root. Reports never include
engine snippets or descriptions, which can contain the matched secret.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | `scan`: a finding at or above `--fail-on` (default `high`) |
| 2 | usage error, skill not found, already installed |
| 3 | `install`: blocked (`dangerous` or `not_scanned`) |
| 4 | `install`: approval missing, rejected, for other content, or by an AI agent |
| 5 | `verify`: drift, or tampered lock or audit log |
| 6 | fetch or engine failure (no verdict) |

## Threat model

Protects against: installing a skill with known-bad patterns; a source that changes between
review and install; an agent approving its own install by accident; silent edits to installed
skills, the lock file or the audit log; secrets leaking into reports.

Does not protect against: a novel malicious skill that no engine detects (static analysis is
incomplete); prompt injection written in plain language (use human review); a hostile process
running as your user (it can rewrite all three files and fake the environment). The strongest
control is a human reviewing the lock-file change in a pull request, with `verify` in CI.

Planned: sandboxed behaviour tests of a skill's scripts (subprocess limits), signed approvals.

## Development

```bash
pip install -e './oss/skill-notary[test]'
pytest oss/skill-notary/tests
ruff check oss/skill-notary && ruff format --check oss/skill-notary
```

The tests build safe, risky and dangerous skills at run time (nothing malicious is stored), serve
them from a local git repository over `file://`, and validate SARIF against the official OASIS
schema (downloaded at a pinned commit, sha256-checked; not redistributed).

## Licence

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for the projects this builds on.
