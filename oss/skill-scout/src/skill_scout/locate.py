"""Find skills (folders with a SKILL.md) inside a fetched tree, without trusting it.

- never follows symlinks; bounded walk (files and depth);
- the frontmatter is read with a regex, never a YAML parser, and only the first 16 KB;
- install names follow the Agent Skills spec (lowercase letters, digits and hyphens, 1-64
  characters, no hyphen at either end): a name is also a folder name, so this is what keeps
  a hostile `name: ../../x` out of the destination.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import UsageError

SKILL_FILE = "SKILL.md"
MAX_WALK_FILES = 20000
MAX_DEPTH = 8
MAX_SKILLS = 1000
FRONTMATTER_MAX_BYTES = 16 * 1024
_NAME_LINE = re.compile(r"^name:\s*['\"]?([^'\"\r\n]+?)['\"]?\s*$", re.MULTILINE)
INSTALL_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


@dataclass(frozen=True)
class SkillDir:
    path: Path
    rel: str  # POSIX path relative to the fetched root ("" for the root itself)
    name: str | None  # `name:` from the frontmatter


def frontmatter_name(skill_md: Path) -> str | None:
    try:
        with skill_md.open("rb") as fh:
            head = fh.read(FRONTMATTER_MAX_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return None
    if not head.startswith("---"):
        return None
    m = _NAME_LINE.search(head[3:].split("\n---", 1)[0])
    return m.group(1).strip() if m else None


def discover(root: Path) -> list[SkillDir]:
    """Every folder below `root` (itself included) with a regular, non-symlink SKILL.md."""
    found: list[SkillDir] = []
    seen = 0
    for dirpath, dirs, files in os.walk(root, followlinks=False):
        base = Path(dirpath)
        rel = base.relative_to(root).as_posix()
        rel = "" if rel == "." else rel
        depth = len(rel.split("/")) if rel else 0
        dirs[:] = sorted(d for d in dirs if d != ".git" and not (base / d).is_symlink()) if depth < MAX_DEPTH else []
        seen += len(files)
        if seen > MAX_WALK_FILES:
            break
        md = base / SKILL_FILE
        if SKILL_FILE in files and md.is_file() and not md.is_symlink():
            found.append(SkillDir(base, rel, frontmatter_name(md)))
            if len(found) >= MAX_SKILLS:
                break
    return sorted(found, key=lambda s: s.rel)


def select(root: Path, name: str | None) -> SkillDir:
    """The skill to install: by frontmatter `name:`, then by folder name; or the only one."""
    skills = discover(root)
    if not skills:
        raise UsageError("no SKILL.md found in the source")
    if name is None:
        if len(skills) == 1:
            return skills[0]
        names = ", ".join(s.name or s.rel for s in skills[:10])
        raise UsageError(f"the source has {len(skills)} skills; pick one with owner/repo@skill ({names})")
    for s in skills:
        if s.name == name:
            return s
    for s in skills:
        if s.path.name == name:
            return s
    raise UsageError(f"skill {name!r} not found in the source")


def install_name(skill: SkillDir) -> str:
    name = skill.name or skill.path.name
    if not INSTALL_NAME.match(name) or "--" in name:
        raise UsageError(f"skill name {name!r} is not a valid Agent Skills name (a-z, 0-9, '-', 1-64)")
    return name
