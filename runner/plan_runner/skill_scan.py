"""SKILL-SCAN-1: scan estático das skills externas candidatas (`agentic-skills-manager`).

O `activate_for_task` (skill_activation.py) pode pesquisar skills externas no skills.sh.
As candidatas são dados não confiáveis, só para revisão humana. Este módulo corre o scan
estático do `agentic-skills-manager` (MIT, PyPI, pin em runner/requirements-test.txt) em
cada uma e junta um veredicto, para o humano não rever às cegas. Nunca instala nada.

Fluxo por candidata (`scan_candidates`):
1. `source` tem de ser `owner/repo` do GitHub (o mesmo que o `npx skills add owner/repo@skill`);
2. clone raso para uma pasta temporária (`github_fetch`): HTTPS só, profundidade 1, sem tags,
   sem hooks, sem a config do sistema nem a do utilizador, sem prompt de credenciais e com um
   ambiente mínimo (nenhum segredo do runner passa para o `git`). Um clone por repo, mesmo com
   várias candidatas do mesmo repo;
3. localiza a pasta da skill: a SKILL.md cujo frontmatter tem `name:` igual ao nome da candidata
   (sem seguir symlinks). Se não a encontra, faz o scan do repo inteiro (`scope: repo`), que
   contém tudo o que um install podia copiar;
4. corre `python -I -m skills_manager scan <pasta> --ci` num processo filho, com timeout e o mesmo
   ambiente mínimo. Só o scan estático: o scanner lê os ficheiros e nunca executa código da skill.
   A revisão por IA (`--ai-checks`) fica desligada: chamaria um CLI de agente pago (claude, codex,
   cursor) com o código não confiável;
5. converte o resultado num veredicto, com o commit analisado e o sha256 da SKILL.md (o
   veredicto vale só para esse conteúdo: um install posterior de outro commit tem de ser
   analisado de novo), e apaga a pasta temporária.

Veredicto (a mesma política por omissão do scanner, que bloqueia high e critical):
- `dangerous`: o scanner bloqueia (alguma finding high ou critical);
- `risky`: passa, mas tem findings medium (rever à mão);
- `safe`: só findings low, ou nenhuma. Não quer dizer confiável: a candidata continua com
  `trusted: false` e `installed: false` (o próprio scanner avisa que um relatório limpo não prova
  que a skill é segura);
- `not_scanned`: não foi possível ter um veredicto (sem scanner, offline, sem source GitHub,
  clone ou scan falhou, orçamento de tempo esgotado). Fail-closed: nunca conta como `safe`.

Nada aqui falha o passo: cada erro fica no veredicto da candidata.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

SCANNER_DIST = "agentic-skills-manager"
SCANNER_MODULE = "skills_manager"
SCANNER_PIN = "1.0.4"  # o mesmo de runner/requirements-test.txt
VERDICTS = ("safe", "risky", "dangerous", "not_scanned")
SEVERITIES = ("low", "medium", "high", "critical")
CLONE_TIMEOUT_S = 60.0
SCAN_TIMEOUT_S = 60.0
TOTAL_BUDGET_S = 240.0
MAX_FINDINGS = 10
LOCATE_MAX_FILES = 5000
LOCATE_MAX_DEPTH = 8
FRONTMATTER_MAX_BYTES = 16 * 1024
FIELD_MAX_CHARS = 200
OFFLINE_ENV = "PLAN_RUNNER_SKILLS_OFFLINE"
# owner do GitHub: 1-39 [A-Za-z0-9-], sem hífen no início; repo: [A-Za-z0-9._-], sem `..`.
_GITHUB_SOURCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}$")
# ANSI escape sequences first: with the single-character class first, ESC alone matched and
# the rest of the sequence ("[31m") stayed in the text.
_CONTROL = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?|[\x00-\x1f\x7f]")
_RULE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_REF = re.compile(r"^refs/[A-Za-z0-9._/-]{1,200}$")
_NAME_LINE = re.compile(r"^name:\s*['\"]?([^'\"\r\n]+?)['\"]?\s*$", re.MULTILINE)
# Só o que o git e o scanner precisam. Nunca as variáveis do runner (chaves, tokens).
_ENV_PASSTHROUGH = (
    "PATH", "LANG", "LC_ALL", "SYSTEMROOT",
    "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy",
    "GIT_SSL_CAINFO", "SSL_CERT_FILE", "SSL_CERT_DIR", "CURL_CA_BUNDLE",
)

FetchFn = Callable[[str, Path], Path]  # ("owner/repo", pasta de destino) -> raiz do clone
ScanFn = Callable[[Path], dict[str, Any]]  # pasta -> JSON do `skills scan --ci`


class ScanError(RuntimeError):
    """Clone ou scan sem resultado utilizável (vai para `reason` do veredicto)."""


def _sanitize(value: Any) -> str:
    return _CONTROL.sub("", str(value or "")).replace("\r", " ").replace("\n", " ").strip()[:FIELD_MAX_CHARS]


def scanner_version() -> str | None:
    """Versão instalada do scanner, ou None se não estiver instalado."""
    if importlib.util.find_spec(SCANNER_MODULE) is None:
        return None
    try:
        return importlib.metadata.version(SCANNER_DIST)
    except importlib.metadata.PackageNotFoundError:
        return None


def _min_env(home: Path) -> dict[str, str]:
    env = {k: os.environ[k] for k in _ENV_PASSTHROUGH if k in os.environ}
    env.update({
        "HOME": str(home), "TMPDIR": str(home),
        "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_LFS_SKIP_SMUDGE": "1", "NO_COLOR": "1",
    })
    return env


def _run(cmd: list[str], *, timeout: float, env: dict[str, str], cwd: Path) -> tuple[int, str]:
    """Corre `cmd` num grupo de processos próprio; no timeout mata o grupo (o `git` lança filhos)."""
    # SEC-2d falso positivo: `cmd` é montado aqui (git ou o scanner), lista sem shell; o único valor
    # externo (owner/repo) passa pela regex _GITHUB_SOURCE e vai depois de `--`.
    # nosemgrep: dangerous-subprocess-use-audit
    proc = subprocess.Popen(  # noqa: S603
        cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        proc.communicate()
        raise ScanError(f"timeout ({timeout:.0f} s)") from None
    return proc.returncode, out or ""


def github_fetch(source: str, dest: Path, timeout: float = CLONE_TIMEOUT_S) -> Path:
    """Clone raso e endurecido de https://github.com/<source> para `dest`."""
    if not _GITHUB_SOURCE.match(source) or ".." in source:
        raise ScanError("source não é owner/repo do GitHub")
    home = dest.parent / f"{dest.name}.home"
    home.mkdir(parents=True, exist_ok=True)
    cmd = [
        "git", "-c", "protocol.allow=never", "-c", "protocol.https.allow=always",
        "-c", "core.hooksPath=/dev/null", "-c", "submodule.recurse=false",
        "clone", "--depth", "1", "--single-branch", "--no-tags", "--quiet",
        "--", f"https://github.com/{source}.git", str(dest),
    ]
    code, _ = _run(cmd, timeout=timeout, env=_min_env(home), cwd=dest.parent)
    if code != 0 or not dest.is_dir():
        raise ScanError(f"git clone falhou (exit {code})")
    return dest


def run_scanner(path: Path, timeout: float = SCAN_TIMEOUT_S) -> dict[str, Any]:
    """`skills scan <path> --ci` (só estático) num processo filho; devolve o JSON do veredicto."""
    cmd = [sys.executable, "-I", "-m", SCANNER_MODULE, "scan", str(path), "--ci"]
    with tempfile.TemporaryDirectory(prefix="skill-scan-home-") as tmp:
        home = Path(tmp)
        code, out = _run(cmd, timeout=timeout, env=_min_env(home), cwd=home)
    lines = [ln for ln in out.splitlines() if ln.strip().startswith("{")]
    try:
        report = json.loads(lines[-1]) if lines else None
    except json.JSONDecodeError:
        report = None
    if not isinstance(report, dict) or not isinstance(report.get("safe"), bool):
        raise ScanError(f"scanner sem veredicto JSON (exit {code})")
    if code not in (0, 1) or (code == 0) != report["safe"]:
        raise ScanError(f"exit {code} não confere com safe={report['safe']}")
    return report


def head_commit(root: Path) -> str | None:
    """sha do commit do clone, lido dos ficheiros do `.git` (sem correr o git). None se não houver."""
    git = root / ".git"
    try:
        head = (git / "HEAD").read_text(encoding="ascii").strip()
        if _SHA1.match(head):
            return head
        ref = head.removeprefix("ref: ").strip()
        if not _REF.match(ref) or ".." in ref:
            return None
        loose = git / ref
        if loose.is_file() and not loose.is_symlink():
            sha = loose.read_text(encoding="ascii").strip()
            return sha if _SHA1.match(sha) else None
        packed = git / "packed-refs"
        for line in packed.read_text(encoding="ascii").splitlines() if packed.is_file() else []:
            sha, _, name = line.partition(" ")
            if name.strip() == ref and _SHA1.match(sha):
                return sha
    except (OSError, UnicodeDecodeError):
        return None
    return None


def _file_sha256(path: Path) -> str | None:
    if not path.is_file() or path.is_symlink():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frontmatter_name(skill_md: Path) -> str | None:
    """`name:` do frontmatter, sem YAML (o ficheiro não é confiável) e com tecto de bytes."""
    try:
        with skill_md.open("rb") as fh:
            head = fh.read(FRONTMATTER_MAX_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return None
    if not head.startswith("---"):
        return None
    block = head[3:].split("\n---", 1)[0]
    m = _NAME_LINE.search(block)
    return m.group(1).strip() if m else None


def locate_skill(root: Path, name: str) -> tuple[Path, str]:
    """(pasta a analisar, scope). `skill`: a pasta da SKILL.md com `name:` igual; senão `repo`."""
    by_dir: Path | None = None
    seen = 0
    for dirpath, dirs, files in os.walk(root, followlinks=False):
        base = Path(dirpath)
        depth = len(base.relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d != ".git" and not (base / d).is_symlink()) if depth < LOCATE_MAX_DEPTH else []
        seen += len(files)
        if seen > LOCATE_MAX_FILES:
            break
        md = base / "SKILL.md"
        if "SKILL.md" not in files or md.is_symlink() or not md.is_file():
            continue
        if _frontmatter_name(md) == name:
            return base, "skill"
        if by_dir is None and base.name == name:
            by_dir = base
    if by_dir is not None:
        return by_dir, "skill"
    return root, "repo"


def verdict_from(report: dict[str, Any]) -> dict[str, Any]:
    """Veredicto a partir do JSON do scanner (findings saneadas: vêm de código não confiável)."""
    counts = dict.fromkeys(SEVERITIES, 0)
    findings: list[dict[str, str]] = []
    for item in report.get("findings") or []:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity") or "medium").lower()
        sev = sev if sev in counts else "medium"
        counts[sev] += 1
        rule = _sanitize(item.get("rule")).lower()
        findings.append({
            "severity": sev,
            "rule": rule if _RULE.match(rule) else "unspecified",
            "path": _sanitize(item.get("path")),
            "issue": _sanitize(item.get("issue")),
        })
    findings.sort(key=lambda f: -SEVERITIES.index(f["severity"]))
    blocked = report.get("safe") is False or counts["high"] > 0 or counts["critical"] > 0
    verdict = "dangerous" if blocked else "risky" if counts["medium"] else "safe"
    top = next((s for s in reversed(SEVERITIES) if counts[s]), None)
    return {"verdict": verdict, "blocked": blocked, "risk_level": top or "none",
            "counts": counts, "findings": findings[:MAX_FINDINGS]}


def _not_scanned(reason: str) -> dict[str, Any]:
    return {"verdict": "not_scanned", "blocked": None, "reason": reason}


def scan_candidates(
    candidates: list[dict[str, Any]],
    *,
    fetch: FetchFn | None = None,
    scan: ScanFn | None = None,
    budget_s: float = TOTAL_BUDGET_S,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Junta `scan` a cada candidata (in-place) e devolve o resumo para `external.scan`.

    `fetch` e `scan` (testes) substituem o clone e o scanner reais.
    """
    version = scanner_version()
    summary: dict[str, Any] = {
        "scanner": f"{SCANNER_DIST} {version}" if version else None,
        "mode": "static",
        "counts": dict.fromkeys(VERDICTS, 0),
        "warnings": [],
    }
    if version and version != SCANNER_PIN:
        summary["warnings"].append(f"scanner_version: {version} instalado, pin {SCANNER_PIN}")
    if not candidates:
        summary["status"] = "no_candidates"
        return summary

    global_reason = None
    if scan is None and version is None:
        global_reason = f"scanner_unavailable: pip install {SCANNER_DIST}=={SCANNER_PIN}"
    elif fetch is None and os.environ.get(OFFLINE_ENV, "").strip() in {"1", "true", "yes"}:
        global_reason = f"offline: {OFFLINE_ENV}=1"
    if global_reason:
        summary["warnings"].append(global_reason)
        for c in candidates:
            c["scan"] = _not_scanned(global_reason)
    else:
        _scan_each(candidates, fetch or github_fetch, scan or run_scanner, budget_s, clock)

    for c in candidates:
        summary["counts"][c["scan"]["verdict"]] += 1
    n = summary["counts"]
    summary["status"] = (
        f"{len(candidates) - n['not_scanned']}/{len(candidates)} analisadas: "
        f"{n['dangerous']} dangerous, {n['risky']} risky, {n['safe']} safe, {n['not_scanned']} not_scanned"
    )
    return summary


def _scan_each(candidates: list[dict[str, Any]], fetch: FetchFn, scan: ScanFn, budget_s: float,
               clock: Callable[[], float]) -> None:
    start = clock()
    clones: dict[str, Path | ScanError] = {}
    with tempfile.TemporaryDirectory(prefix="skill-scan-") as tmp:
        tmp_root = Path(tmp)
        for i, c in enumerate(candidates):
            source = str(c.get("source") or "")
            if not _GITHUB_SOURCE.match(source) or ".." in source:
                c["scan"] = _not_scanned("sem source owner/repo do GitHub")
                continue
            if clock() - start > budget_s:
                c["scan"] = _not_scanned(f"budget: mais de {budget_s:.0f} s no scan das candidatas")
                continue
            if source not in clones:
                try:
                    clones[source] = fetch(source, tmp_root / f"repo-{i}")
                except Exception as e:  # noqa: BLE001 -- rede/git nunca falha o passo
                    clones[source] = e if isinstance(e, ScanError) else ScanError(type(e).__name__)
            root = clones[source]
            if isinstance(root, ScanError):
                c["scan"] = _not_scanned(f"fetch: {root}")
                continue
            target, scope = locate_skill(root, str(c.get("name") or ""))
            try:
                result = verdict_from(scan(target))
            except Exception as e:  # noqa: BLE001 -- o scanner nunca falha o passo
                c["scan"] = _not_scanned(f"scan: {e if isinstance(e, ScanError) else type(e).__name__}")
                continue
            rel = target.relative_to(root).as_posix()
            c["scan"] = {**result, "scope": scope, "path": "" if rel == "." else rel,
                         "commit": head_commit(root), "skill_sha256": _file_sha256(target / "SKILL.md")}
