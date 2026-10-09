# auditron

**One defensive security gate for a repository.** Runs `pip-audit` (dependency CVEs),
`bandit` (Python SAST) and `zizmor` (GitHub Actions security) in a single pass, normalizes every
finding into one model, writes **one report** (JSON + SARIF 2.1.0), and exits 0/1 by a policy you
declare. Self-contained and pluggable: `pip install auditron` + one workflow, in any repo.

> Defensive by design: auditron only reads and reports — it never attacks or runs exploits.
> Offensive tooling (pentest, LLM red-team) are documented lab companions, not part of this package
> (see [Companions](#companions)).

## Quickstart

```bash
pip install auditron
auditron scan .                      # scan the repo; exit 1 if a blocking engine finds something
auditron scan . --sarif out.sarif    # emit SARIF 2.1.0 for GitHub code scanning
auditron scan . --only bandit        # run a single engine
```

Drop it into CI (copy `examples/auditron.yml` into `.github/workflows/`):

```yaml
- run: pip install auditron
- run: auditron scan . --sarif auditron.sarif
- uses: github/codeql-action/upload-sarif@<pinned>   # optional: findings as code-scanning alerts
  with: { sarif_file: auditron.sarif }
```

## What it bundles

| Engine | License | Covers | SARIF level |
|---|---|---|---|
| [pip-audit](https://github.com/pypa/pip-audit) | Apache-2.0 | known CVEs in `requirements*.txt` | error |
| [bandit](https://github.com/PyCQA/bandit) | Apache-2.0 | Python SAST (`-ll -ii`, medium+) | HIGH→error, MEDIUM→warning, LOW→note |
| [zizmor](https://github.com/zizmorcore/zizmor) | MIT/Apache-2.0 | GitHub Actions security | passthrough |

The exact version of each engine is recorded in every report and in each SARIF `run`, so the
evidence is reproducible.

## Policy (`auditron.toml`)

Without a config, the default is: all three engines run; **only `pip-audit` blocks** (a known CVE in
a dependency is factual), while `bandit`/`zizmor` report until the repo triages their findings. Override
per engine:

```toml
[auditron]
blocking = ["pip-audit", "bandit"]   # which engines fail the gate
disabled = ["zizmor"]                 # which engines don't run at all
```

An engine that **errors** (not installed, bad output) never passes silently: if it is blocking, it
blocks — absence of evidence is not evidence of absence.

## Why auditron

Three first-class scanners already exist and are excellent. What is missing in most repos is the
*glue*: one install, one command, one policy, one SARIF, one exit code — and a design that lets you
lift it into its own repository unchanged. auditron is that glue, and nothing more. See
[POSITIONING.md](POSITIONING.md) for the honest comparison with rolling your own, with `pre-commit`,
and with hosted scanners.

## Companions (offensive, lab-only)

auditron is defensive. For adversarial testing, use these **in a lab**, never in the production gate:

- **Strix** (pentest de app, confirma falhas com PoC) — `docs/ops/STRIX-LAB.md` no projecto-mãe.
- **Garak / promptfoo** (red-team de LLM: prompt injection, jailbreak) — `docs/ops/SECURITY-TOOLS.md`.

## License

MIT (see `LICENSE`). Bundled engines keep their own licenses (`NOTICE`).
