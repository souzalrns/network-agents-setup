"""Agent Skills specification checks (https://agentskills.io/specification), built in.

The same ground the `skill-guard` PR gate covers for format, kept to what the spec states:
- SKILL.md starts with YAML frontmatter;
- `name`: required, 1-64 characters, lowercase letters, digits and hyphens, no hyphen at
  either end, no `--`, and equal to the folder name;
- `description`: required, 1-1024 characters;
- `compatibility`: at most 500 characters.

A skill an agent may not load correctly (no frontmatter, no or invalid name, no description)
is `medium`: it needs a human look. Cosmetic mismatches are `low`. The frontmatter is read
with regexes, never a YAML parser (the file is untrusted).
"""

from __future__ import annotations

import re
from pathlib import Path

from .engines import Finding
from .locate import FRONTMATTER_MAX_BYTES, INSTALL_NAME, SKILL_FILE, SkillDir

SPEC_URI = "https://agentskills.io/specification"
_FIELD = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*):[ \t]*(?P<value>.*)$")


def _frontmatter(md: Path) -> dict[str, str] | None:
    try:
        with md.open("rb") as fh:
            head = fh.read(FRONTMATTER_MAX_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return None
    if not head.startswith("---"):
        return None
    block = head[3:].split("\n---", 1)[0]
    fields: dict[str, str] = {}
    key = None
    for line in block.splitlines():
        m = _FIELD.match(line)
        if m:
            key = m["key"]
            fields[key] = m["value"].strip().strip("'\"")
        elif key and line[:1] in (" ", "\t"):  # folded / literal continuation
            fields[key] = (fields[key].lstrip(">|-").strip() + " " + line.strip()).strip()
    return fields


def _f(rule: str, severity: str, rel: str, title: str, fix: str) -> Finding:
    return Finding("spec", rule, severity, f"{rel}/{SKILL_FILE}" if rel else SKILL_FILE, title, fix)


def check(skill: SkillDir) -> list[Finding]:
    rel = skill.rel
    fm = _frontmatter(skill.path / SKILL_FILE)
    if fm is None:
        return [
            _f(
                "missing-frontmatter",
                "medium",
                rel,
                "SKILL.md has no YAML frontmatter",
                "Start SKILL.md with --- name: … description: … ---",
            )
        ]
    out: list[Finding] = []
    name = fm.get("name", "")
    if not name:
        out.append(_f("missing-name", "medium", rel, "Frontmatter has no `name`", "Add `name:` (a-z, 0-9, '-')."))
    elif not INSTALL_NAME.match(name) or "--" in name:
        out.append(
            _f(
                "invalid-name",
                "medium",
                rel,
                f"`name` {name[:64]!r} breaks the spec",
                "Use 1-64 lowercase letters, digits and single hyphens, no hyphen at either end.",
            )
        )
    elif skill.path.name != name:
        out.append(
            _f(
                "name-folder-mismatch",
                "low",
                rel,
                f"`name` {name!r} differs from the folder name",
                "Rename the folder (or the name) so they match.",
            )
        )
    desc = fm.get("description", "")
    if not desc:
        out.append(
            _f(
                "missing-description",
                "medium",
                rel,
                "Frontmatter has no `description`",
                "Describe what the skill does and when to use it (max 1024 characters).",
            )
        )
    elif len(desc) > 1024:
        out.append(
            _f(
                "description-too-long",
                "low",
                rel,
                f"`description` has {len(desc)} characters (max 1024)",
                "Shorten the description.",
            )
        )
    if len(fm.get("compatibility", "")) > 500:
        out.append(
            _f("compatibility-too-long", "low", rel, "`compatibility` is longer than 500 characters", "Shorten it.")
        )
    return out
