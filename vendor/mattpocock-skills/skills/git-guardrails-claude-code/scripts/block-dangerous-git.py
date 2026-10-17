#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive or history-rewriting git commands before they run.

Adapted for network-agents-setup from mattpocock/skills (git-guardrails-claude-code, MIT). The upstream hook
blocks every `git push`; this one lets a normal push to a feature branch through (the PR workflow needs it) and
blocks what the maestro's rules forbid: force pushes, pushes to main/master, rebase and other history rewrites,
and commands that throw work away. Reads the hook JSON on stdin; exit 2 blocks (the reason goes to stderr).
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

PROTECTED = {"main", "master"}
GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def _segments(command: str) -> list[list[str]]:
    """Split on shell separators, then tokenise each piece (best effort; unparsable text is kept whole)."""
    out = []
    for part in re.split(r"&&|\|\||[;|\n]", command):
        try:
            tokens = shlex.split(part, posix=True)
        except ValueError:
            tokens = part.split()
        if tokens:
            out.append(tokens)
    return out


def _git_call(tokens: list[str]) -> tuple[str, list[str]] | None:
    """(subcommand, args) when the segment runs git, skipping env assignments, sudo and git's global options."""
    i = 0
    while i < len(tokens) and (re.match(r"^\w+=", tokens[i]) or tokens[i] in ("sudo", "command", "env")):
        i += 1
    if i >= len(tokens) or tokens[i].rsplit("/", 1)[-1] != "git":
        return None
    i += 1
    while i < len(tokens) and tokens[i].startswith("-"):
        opt = tokens[i].split("=", 1)[0]
        i += 2 if opt in GLOBAL_OPTS_WITH_VALUE and "=" not in tokens[i] else 1
    if i >= len(tokens):
        return None
    return tokens[i], tokens[i + 1 :]


def _push_problem(args: list[str]) -> str | None:
    flags = [a for a in args if a.startswith("-")]
    for f in flags:
        if f in ("-f", "--force", "--mirror", "--delete", "-d", "--prune") or f.startswith(
            ("--force-with-lease", "--force-if-includes")
        ):
            return f"`git push {f}` rewrites or deletes remote history"
        if re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", f):
            return f"`git push {f}` includes -f (force)"
    refspecs = [a for a in args if not a.startswith("-")][1:]  # first positional is the remote
    if not refspecs or refspecs == ["HEAD"]:  # pushes the current branch: is it main/master?
        branch = _current_branch()
        if branch in PROTECTED:
            return f"you are on `{branch}`: a bare push would go straight to it; open a PR instead"
    for ref in refspecs:
        if ref.startswith("+"):
            return f"`+{ref[1:]}` is a force push"
        if ref.startswith(":"):
            return f"`{ref}` deletes a remote branch"
        dest = ref.split(":", 1)[-1].removeprefix("refs/heads/")
        if dest in PROTECTED:
            return f"pushing to `{dest}` directly: open a PR instead"
    return None


def _current_branch() -> str | None:
    """The checked-out branch, read from .git/HEAD (no subprocess); None when unknown or detached."""
    here = Path.cwd().resolve()  # hooks run in the project directory
    for d in (here, *here.parents):
        git = d / ".git"
        if git.is_file():  # worktree or submodule: "gitdir: <path>"
            line = git.read_text(encoding="utf-8").strip()
            git = (d / line.removeprefix("gitdir:").strip()).resolve()
        if (git / "HEAD").is_file():
            head = (git / "HEAD").read_text(encoding="utf-8").strip()
            return head.removeprefix("ref: refs/heads/") if head.startswith("ref: refs/heads/") else None
    return None


def problem(command: str) -> str | None:
    for tokens in _segments(command):
        call = _git_call(tokens)
        if not call:
            continue
        sub, args = call
        if sub == "push":
            why = _push_problem(args)
        elif sub == "rebase":
            why = "`git rebase` rewrites history (rule: no rebase)"
        elif sub in ("filter-branch", "filter-repo"):
            why = f"`git {sub}` rewrites history"
        elif sub == "reset" and "--hard" in args:
            why = "`git reset --hard` throws away uncommitted work"
        elif sub == "clean" and any(re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) or a == "--force" for a in args):
            why = "`git clean -f` deletes untracked files"
        elif sub == "branch" and ("-D" in args or ("--delete" in args and "--force" in args)):
            why = "`git branch -D` deletes a branch that may not be merged"
        elif sub in ("checkout", "restore") and "." in args:
            why = f"`git {sub} .` throws away every local change"
        else:
            why = None
        if why:
            return why
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0  # not a hook payload: nothing to judge
    command = ((data or {}).get("tool_input") or {}).get("command") or ""
    why = problem(command)
    if why:
        print(f"BLOCKED by git guardrails: {why}. The maestro has not authorised this; ask first.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
