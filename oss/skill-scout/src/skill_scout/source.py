"""Where a skill comes from, and how it is fetched into a throwaway workspace.

Sources:
- `owner/repo@skill`: the `npx skills add` syntax (skills.sh); `owner/repo` alone means the
  whole repository. `https://github.com/owner/repo` is accepted too;
- a local directory (`./path`, `../path`, `/abs/path`).

Fetching never runs code from the source. GitHub sources use git over HTTPS only:
`git init` + `git fetch --depth 1 <url> <ref>` + `checkout FETCH_HEAD`, with no hooks, no
system or user git config, no credential prompt, no LFS smudge and a minimal environment
(no variable of the caller, such as API keys, reaches git). The commit comes from
`.git/FETCH_HEAD`; the `.git` folder is then deleted, so the scanners and the install only
ever see the working tree.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from .errors import FetchError, UsageError

GITHUB = "https://github.com"
FETCH_TIMEOUT_S = 120.0
_OWNER = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})"
_REPO = r"[A-Za-z0-9._-]{1,100}"
_SKILL = r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}"
_GITHUB_SPEC = re.compile(rf"^(?P<owner>{_OWNER})/(?P<repo>{_REPO})(?:@(?P<skill>{_SKILL}))?$")
_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
# Only what git needs to reach the network. Never the caller's secrets.
_ENV_PASSTHROUGH = (
    "PATH",
    "LANG",
    "LC_ALL",
    "SYSTEMROOT",
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "NO_PROXY",
    "no_proxy",
    "GIT_SSL_CAINFO",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "CURL_CA_BUNDLE",
)


@dataclass(frozen=True)
class Source:
    kind: str  # "github" | "local"
    raw: str
    owner: str | None = None
    repo: str | None = None
    skill: str | None = None
    ref: str | None = None
    path: Path | None = None

    @property
    def repo_url(self) -> str | None:
        return f"{GITHUB}/{self.owner}/{self.repo}" if self.kind == "github" else None

    @property
    def display(self) -> str:
        if self.kind == "local":
            return self.raw  # as typed: never the resolved absolute path (it would leak the user name)
        spec = f"{self.owner}/{self.repo}" + (f"@{self.skill}" if self.skill else "")
        return spec + (f"#{self.ref}" if self.ref else "")


def parse_source(raw: str, ref: str | None = None) -> Source:
    raw = (raw or "").strip()
    if not raw:
        raise UsageError("empty source")
    if ref is not None and (not _REF.match(ref) or ".." in ref):
        raise UsageError(f"invalid --ref: {ref!r}")
    if raw.startswith(("./", "../", "/", "~")) or raw in {".", ".."}:
        path = Path(raw).expanduser().resolve()
        if not path.is_dir():
            raise UsageError(f"local source is not a directory: {raw}")
        if ref:
            raise UsageError("--ref only applies to GitHub sources")
        return Source("local", raw, path=path)
    spec = raw
    for prefix in (f"{GITHUB}/", "github.com/"):
        if spec.startswith(prefix):
            spec = spec[len(prefix) :]
    spec = spec.removesuffix("/").removesuffix(".git") if "@" not in spec else spec
    m = _GITHUB_SPEC.match(spec)
    if not m or m["repo"] in {".", ".."} or ".." in m["repo"]:
        raise UsageError(f"source must be owner/repo[@skill] or a local directory: {raw!r}")
    repo = m["repo"].removesuffix(".git")
    return Source("github", raw, owner=m["owner"], repo=repo, skill=m["skill"], ref=ref)


# --------------------------------------------------------------------------- processes


def minimal_env(home: Path) -> dict[str, str]:
    env = {k: os.environ[k] for k in _ENV_PASSTHROUGH if k in os.environ}
    env.update(
        {
            "HOME": str(home),
            "TMPDIR": str(home),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_LFS_SKIP_SMUDGE": "1",
            "GIT_PROTOCOL_FROM_USER": "0",
            "NO_COLOR": "1",
        }
    )
    return env


def run(cmd: list[str], *, timeout: float, env: dict[str, str], cwd: Path) -> tuple[int, str, str]:
    """Run `cmd` in its own process group; on timeout kill the whole group (git spawns children)."""
    # The command lists are built in this package (git or a scanner), never through a shell.
    # nosemgrep: dangerous-subprocess-use-audit
    proc = subprocess.Popen(  # noqa: S603
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        proc.communicate()
        raise FetchError(f"timeout after {timeout:.0f} s: {cmd[0]}") from None
    return proc.returncode, out or "", err or ""


# --------------------------------------------------------------------------- fetch


@dataclass(frozen=True)
class Fetched:
    root: Path
    commit: str | None


def fetch(source: Source, dest: Path, *, base_url: str = GITHUB, timeout: float = FETCH_TIMEOUT_S) -> Fetched:
    """Materialise `source` in `dest` (which must not exist). Local sources are copied."""
    dest = Path(dest)
    if source.kind == "local":
        if source.path is None:
            raise UsageError("local source without a path")
        root = source.path
        shutil.copytree(root, dest, symlinks=True, ignore=lambda d, names: [".git"] if Path(d) == root else [])
        return Fetched(dest, None)
    return _fetch_git(source, dest, base_url=base_url, timeout=timeout)


def _fetch_git(source: Source, dest: Path, *, base_url: str, timeout: float) -> Fetched:
    scheme = urllib.parse.urlsplit(base_url).scheme
    if scheme not in {"https", "file"}:
        raise FetchError(f"unsupported git transport: {scheme or base_url}")
    url = f"{base_url.rstrip('/')}/{source.owner}/{source.repo}"
    hardening = [
        "-c",
        "protocol.allow=never",
        "-c",
        f"protocol.{scheme}.allow=always",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "submodule.recurse=false",
        "-c",
        "fetch.recurseSubmodules=false",
        "-c",
        "core.fsmonitor=false",
    ]
    with tempfile.TemporaryDirectory(prefix="skill-scout-git-home-") as home_dir:
        env = minimal_env(Path(home_dir))
        dest.mkdir(parents=True)
        steps = [
            ("init", ["git", *hardening, "init", "--quiet", str(dest)]),
            (
                "fetch",
                [
                    "git",
                    *hardening,
                    "-C",
                    str(dest),
                    "fetch",
                    "--depth",
                    "1",
                    "--no-tags",
                    "--quiet",
                    "--",
                    url,
                    source.ref or "HEAD",
                ],
            ),
            ("checkout", ["git", *hardening, "-C", str(dest), "checkout", "--quiet", "--detach", "FETCH_HEAD"]),
        ]
        for step, cmd in steps:
            code, _, err = run(cmd, timeout=timeout, env=env, cwd=Path(home_dir))
            if code != 0:
                last = (err.strip().splitlines() or [""])[-1][:200]
                raise FetchError(f"git {step} failed for {source.display} (exit {code}): {last}")
    commit = _fetch_head_commit(dest / ".git")
    if (dest / ".git").exists():
        shutil.rmtree(dest / ".git")
    return Fetched(dest, commit)


def _fetch_head_commit(git_dir: Path) -> str | None:
    try:
        first = (git_dir / "FETCH_HEAD").read_text(encoding="ascii", errors="replace").split()[0]
    except (OSError, IndexError):
        return None
    return first if _SHA1.match(first) else None
