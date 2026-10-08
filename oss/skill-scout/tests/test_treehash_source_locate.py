"""Content hash, source parsing, hardened fetch (real git over file://) and skill discovery."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from skill_scout import source as src_mod
from skill_scout.errors import FetchError, UsageError
from skill_scout.locate import discover, frontmatter_name, install_name, select
from skill_scout.source import fetch, parse_source
from skill_scout.treehash import TREE_ALGO, tree_hash

from .helpers import make_safe, monorepo, skill_md, write

# --------------------------------------------------------------------------- tree hash


def test_hash_is_deterministic_and_order_independent(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for name in ("z.md", "B.md", "a.md", "dir/é.md"):  # created in different orders
        write(a / name, name)
    for name in ("dir/é.md", "a.md", "B.md", "z.md"):
        write(b / name, name)
    ha, hb = tree_hash(a), tree_hash(b)
    assert ha.digest == hb.digest and len(ha.digest) == 64
    assert [e.path for e in ha.entries] == ["B.md", "a.md", "dir/é.md", "z.md"]  # code point, not locale
    assert ha.to_json()["algorithm"] == TREE_ALGO and ha.files == 4


@pytest.mark.parametrize("change", ["content", "add", "remove", "exec", "rename"])
def test_any_change_changes_the_hash(tmp_path, change):
    d = make_safe(tmp_path / "s")
    before = tree_hash(d).digest
    if change == "content":
        (d / "SKILL.md").write_text("x", encoding="utf-8")
    elif change == "add":
        write(d / "new.txt", "x")
    elif change == "remove":
        (d / "references" / "guide.md").unlink()
    elif change == "exec":
        (d / "SKILL.md").chmod(0o755)
    else:
        (d / "references" / "guide.md").rename(d / "references" / "guide2.md")
    assert tree_hash(d).digest != before


def test_newline_in_a_file_name_cannot_forge_entries(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    write(a / "x\n", "1")
    write(b / "x", "1")
    assert tree_hash(a).digest != tree_hash(b).digest


def test_symlinks_and_root_git_are_not_hashed(tmp_path):
    d = make_safe(tmp_path / "s")
    plain = tree_hash(d).digest
    write(d / ".git" / "HEAD", "ref: refs/heads/main\n")
    assert tree_hash(d).digest == plain  # root .git is fetch metadata
    (d / "link").symlink_to(d / "SKILL.md")
    os.mkfifo(d / "pipe")
    t = tree_hash(d)
    assert t.digest == plain and t.unsupported == ("link (symlink)", "pipe (special file)")


def test_too_large_is_refused(tmp_path, monkeypatch):
    from skill_scout import treehash

    d = make_safe(tmp_path / "s")
    write(d / "x", "x")
    monkeypatch.setattr(treehash, "MAX_FILES", 2)
    with pytest.raises(UsageError, match="too large"):
        tree_hash(d)
    monkeypatch.setattr(treehash, "MAX_FILES", 100)
    monkeypatch.setattr(treehash, "MAX_BYTES", 10)
    with pytest.raises(UsageError, match="too large"):
        tree_hash(d)


# --------------------------------------------------------------------------- source


@pytest.mark.parametrize(
    "raw, owner, repo, skill",
    [
        ("vercel-labs/agent-skills@react-best-practices", "vercel-labs", "agent-skills", "react-best-practices"),
        ("anthropics/skills", "anthropics", "skills", None),
        ("https://github.com/anthropics/skills", "anthropics", "skills", None),
        ("github.com/anthropics/skills.git", "anthropics", "skills", None),
    ],
)
def test_github_sources(raw, owner, repo, skill):
    s = parse_source(raw)
    assert (s.kind, s.owner, s.repo, s.skill) == ("github", owner, repo, skill)
    assert s.repo_url == f"https://github.com/{owner}/{repo}"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "a",
        "a/b/c",
        "-a/b",
        "a/..",
        "a/b@",
        "a/b@../x",
        "a b/c",
        "git@github.com:a/b",
        "a/b;rm -rf /",
        "a/b@x y",
        "https://evil.example/a/b",
    ],
)
def test_bad_sources_are_refused(raw):
    with pytest.raises(UsageError):
        parse_source(raw)


@pytest.mark.parametrize("ref", ["-x", "a..b", "a b", "--upload-pack=x", ""])
def test_bad_refs_are_refused(ref):
    with pytest.raises(UsageError):
        parse_source("a/b", ref)


def test_local_source_display_never_leaks_the_absolute_path(tmp_path, monkeypatch):
    make_safe(tmp_path / "s")
    monkeypatch.chdir(tmp_path)
    s = parse_source("./s")
    assert s.kind == "local" and s.display == "./s" and s.path == (tmp_path / "s").resolve()
    with pytest.raises(UsageError):
        parse_source("./missing")
    with pytest.raises(UsageError, match="--ref"):
        parse_source("./s", "main")


def test_real_fetch_by_branch_tag_and_commit(github, tmp_path):
    first = github.repo("acme", "skills", monorepo)
    second = github.commit("acme", "skills", lambda w: write(w / "skills" / "good" / "extra.md", "v2"))
    got = fetch(parse_source("acme/skills"), tmp_path / "head", base_url=github.base_url)
    assert got.commit == second and (got.root / "skills" / "good" / "extra.md").is_file()
    assert not (got.root / ".git").exists()  # scanners and install never see git metadata
    old = fetch(parse_source("acme/skills", first), tmp_path / "old", base_url=github.base_url)
    assert old.commit == first and not (old.root / "skills" / "good" / "extra.md").exists()
    main = fetch(parse_source("acme/skills", "main"), tmp_path / "main", base_url=github.base_url)
    assert main.commit == second


def test_fetch_errors_are_fetch_errors(github, tmp_path):
    with pytest.raises(FetchError, match="git fetch failed"):
        fetch(parse_source("acme/missing"), tmp_path / "x", base_url=github.base_url)
    with pytest.raises(FetchError, match="transport"):
        fetch(parse_source("acme/skills"), tmp_path / "y", base_url="http://github.com")


def test_fetch_command_is_hardened_and_gets_no_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-pass")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-pass")
    calls = []

    def fake_run(cmd, *, timeout, env, cwd):
        calls.append((cmd, env))
        return 0, "", ""

    monkeypatch.setattr(src_mod, "run", fake_run)
    got = fetch(parse_source("acme/skills@good", "v1.2"), tmp_path / "r")
    assert got.commit is None  # no FETCH_HEAD was written by the fake git
    init, fetch_cmd, checkout = (c for c, _ in calls)
    assert fetch_cmd[-3:] == ["--", "https://github.com/acme/skills", "v1.2"]
    assert {"--depth", "--no-tags"} <= set(fetch_cmd)
    for flag in (
        "protocol.allow=never",
        "protocol.https.allow=always",
        "core.hooksPath=/dev/null",
        "submodule.recurse=false",
        "core.fsmonitor=false",
    ):
        assert flag in init and flag in fetch_cmd and flag in checkout
    for _, env in calls:
        assert "GITHUB_TOKEN" not in env and "ANTHROPIC_API_KEY" not in env
        assert env["GIT_TERMINAL_PROMPT"] == "0" and env["GIT_CONFIG_GLOBAL"] == os.devnull
        assert env["HOME"] != os.environ.get("HOME")


def test_timeout_kills_the_process_group(tmp_path):
    import sys
    import time

    child = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])"
    t0 = time.monotonic()
    with pytest.raises(FetchError, match="timeout"):
        src_mod.run([sys.executable, "-c", child + "; time.sleep(30)"], timeout=0.5, env=dict(os.environ), cwd=tmp_path)
    assert time.monotonic() - t0 < 10


# --------------------------------------------------------------------------- locate


def test_discover_and_select(tmp_path):
    monorepo(tmp_path)
    assert [s.rel for s in discover(tmp_path)] == ["skills/envy-dir", "skills/evil", "skills/good"]
    assert select(tmp_path, "envy").rel == "skills/envy-dir"  # by frontmatter name
    assert select(tmp_path, "envy-dir").rel == "skills/envy-dir"  # by folder name
    with pytest.raises(UsageError, match="3 skills"):
        select(tmp_path, None)
    with pytest.raises(UsageError, match="not found"):
        select(tmp_path, "ghost")
    only = make_safe(tmp_path / "one")
    assert select(only, None).path == only


def test_symlinked_skill_md_is_ignored(tmp_path):
    outside = make_safe(tmp_path / "outside", name="linked")
    (tmp_path / "r" / "x").mkdir(parents=True)
    (tmp_path / "r" / "x" / "SKILL.md").symlink_to(outside / "SKILL.md")
    (tmp_path / "r" / "y").symlink_to(outside, target_is_directory=True)
    assert discover(tmp_path / "r") == []


@pytest.mark.parametrize(
    "name, ok",
    [
        ("good", True),
        ("a-b-1", True),
        ("../../x", False),
        ("A", False),
        ("-a", False),
        ("a-", False),
        ("a--b", False),
        ("x" * 65, False),
    ],
)
def test_install_names_follow_the_spec(tmp_path, name, ok):
    write(tmp_path / "SKILL.md", skill_md(name))
    skill = select(tmp_path, None)
    assert frontmatter_name(tmp_path / "SKILL.md") == name
    if ok:
        assert install_name(skill) == name
    else:
        with pytest.raises(UsageError, match="valid Agent Skills name"):
            install_name(skill)


def test_frontmatter_is_read_without_yaml_and_bounded(tmp_path):
    write(tmp_path / "a" / "SKILL.md", "---\nname: 'quoted'\nother: !!python/object:os.system x\n---\n")
    assert frontmatter_name(tmp_path / "a" / "SKILL.md") == "quoted"
    write(tmp_path / "b" / "SKILL.md", "---\n" + "x: y\n" * 5000 + "name: late\n---\n")
    assert frontmatter_name(tmp_path / "b" / "SKILL.md") is None
    assert frontmatter_name(Path(tmp_path / "missing.md")) is None
