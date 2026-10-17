"""Incorpora 6 skills de mattpocock/skills (MIT), adaptadas às regras do setup.

Uso (a partir da raiz do repo; o checkout tem de estar no commit indicado):

    git clone https://github.com/mattpocock/skills /tmp/mattpocock-skills
    git -C /tmp/mattpocock-skills checkout <commit>
    python scripts/vendor_mattpocock_skills.py --src /tmp/mattpocock-skills --commit <commit>

Gera (e reescreve; não editar à mão):

- ``vendor/mattpocock-skills/skills/<nome>/``: as 6 skills, já adaptadas, com LICENSE e PROVENANCE.md.
  É daqui que o ``skill-scout`` instala no Claude Code (``.claude/skills`` do repo de destino).
- ``scripts/install-mattpocock-skills.sh``: o comando que o maestro corre, com os hashes aprovados.

Escolha e adaptações (decisão do maestro, 2026-10-14, opção A): só as skills que o setup não cobria. As
adaptações são dirigidas: cada substituição tem de encontrar o texto esperado; se o upstream mudar, o
script falha em vez de deixar passar conteúdo não revisto. Os ficheiros inteiramente nossos vêm de
``scripts/mattpocock_overlays/<skill>/`` e sobrepõem-se ao upstream.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess  # nosec B404 - só `git rev-parse` no checkout dado
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "mattpocock/skills"
VENDOR = ROOT / "vendor" / "mattpocock-skills"
OVERLAYS = ROOT / "scripts" / "mattpocock_overlays"

# nome -> (caminho no upstream, porque entra)
SELECTED: dict[str, tuple[str, str]] = {
    "wizard": ("skills/engineering/wizard", "guia bash para o que só o humano faz (chaves, dashboards, secrets)"),
    "git-guardrails-claude-code": (
        "skills/misc/git-guardrails-claude-code",
        "hook que bloqueia --force, push para main, rebase e comandos que deitam trabalho fora",
    ),
    "handoff": ("skills/productivity/handoff", "passa a conversa a outro agente, sem segredos"),
    "retro": ("skills/engineering/retro", "retrospectiva da sessão: melhorias ao ambiente do agente"),
    "writing-for-agents": ("skills/productivity/writing-for-agents", "como escrever skills e CLAUDE.md"),
    "to-questionnaire": ("skills/productivity/to-questionnaire", "decisão que precisa de outra pessoa → questionário"),
}

WIZARD_RULES = """
## Rules in this setup (network-agents-setup)

- Secrets go only to the environment, to a **git-ignored** `.env`, or to `gh secret set`. The library's
  `write_env` refuses an env file that git does not ignore (it would end up in a commit); never weaken that.
- Keep wizards ephemeral (scratch dir or `scripts/` outside version control) unless the maestro asks for a
  repeatable setup path. A committed wizard holds stages and URLs, never values.
- A stage that touches production (Vercel/Supabase secrets, SQL, live exchange keys) needs its own
  `confirm` gate naming the production target. Live trading keys are out of scope: L4 is blocked.
"""

WIZARD_GUARD = """# _env_ignored: true when ENV_FILE will not be committed (git ignores it, or this is not a git repo).
# Added in network-agents-setup: a secret must never land in a tracked file.
_env_ignored() {
  command -v git >/dev/null 2>&1 || return 0
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0
  git check-ignore -q -- "$ENV_FILE"
}

# write_env KEY VALUE upserts KEY='VALUE' into ENV_FILE (replaces any existing
"""

PATCHES: dict[str, list[tuple[str, str, str]]] = {
    "wizard": [
        (
            "SKILL.md",
            "## Process\n",
            WIZARD_RULES.lstrip("\n") + "\n## Process\n",
        ),
        (
            "template.sh",
            "# write_env KEY VALUE upserts KEY='VALUE' into ENV_FILE (replaces any existing\n",
            WIZARD_GUARD,
        ),
        (
            "template.sh",
            '  local key="$1" value="$2" tmp sq="\'\\\\\'\'"\n',
            '  local key="$1" value="$2" tmp sq="\'\\\\\'\'"\n'
            "  if ! _env_ignored; then\n"
            '    warn "refusing to write $key: $ENV_FILE is not git-ignored. Add it to .gitignore and re-run;"\n'
            '    warn "values already saved are kept, and the wizard stops here (set -e)."\n'
            "    return 1\n"
            "  fi\n",
        ),
    ],
    "to-questionnaire": [
        (
            "SKILL.md",
            "Write it to `to-questionnaire-<slug>.md` in the current directory (slug from the topic) and report the path.",
            "Write it to `to-questionnaire-<slug>.md` (slug from the topic) in the path the user names, else in the OS "
            "temp dir (`$TMPDIR`, else `/tmp`), and report the path. Never inside `docs/knowledge/` (it is ingested "
            "into the production RAG) and never commit it: it may carry a client's or a partner's private context.",
        ),
    ],
}

# Ficheiros do upstream que as adaptações substituem por completo (o overlay traz o novo).
DROP = {"git-guardrails-claude-code": ["scripts/block-dangerous-git.sh"]}


def _git_head(src: Path) -> str:
    out = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)  # nosec B603 B607
    return out.stdout.strip()


def vendor(src: Path) -> dict[str, str]:
    if VENDOR.exists():
        shutil.rmtree(VENDOR)
    (VENDOR / "skills").mkdir(parents=True)
    digests = {}
    for name, (rel, _why) in SELECTED.items():
        dst = VENDOR / "skills" / name
        shutil.copytree(src / rel, dst)
        for drop in DROP.get(name, []):
            (dst / drop).unlink()
        for file, old, new in PATCHES.get(name, []):
            path = dst / file
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{name}/{file}: o texto a adaptar mudou no upstream; rever a adaptação")
            path.write_text(text.replace(old, new), encoding="utf-8")
        overlay = OVERLAYS / name
        if overlay.exists():
            for f in overlay.rglob("*"):
                if f.is_file() and "__pycache__" not in f.parts:
                    target = dst / f.relative_to(overlay)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, target)
        digests[name] = hashlib.sha256((dst / "SKILL.md").read_bytes()).hexdigest()
    shutil.copy2(src / "LICENSE", VENDOR / "LICENSE")
    return digests


def provenance(commit: str, digests: dict[str, str]) -> None:
    adapted = {**{n: "texto" for n in PATCHES}, **{n: "ficheiros nossos" for n in DROP}}
    rows = "\n".join(
        f"| `{n}` | {SELECTED[n][1]} | {adapted.get(n, 'não')} | `{d[:12]}` |" for n, d in digests.items()
    )
    (VENDOR / "PROVENANCE.md").write_text(
        "# Proveniência de `vendor/mattpocock-skills/`\n\n"
        "> Gerado por `scripts/vendor_mattpocock_skills.py`. Não editar à mão: correr o script outra vez.\n\n"
        f"- **Origem:** [{UPSTREAM}](https://github.com/{UPSTREAM}) (MIT, ver `LICENSE`)\n"
        f"- **Commit:** `{commit}`\n"
        f"- **Skills:** {len(digests)} de 38 (decisão do maestro, 2026-10-14, opção A). As outras ficaram de\n"
        "  fora por já terem equivalente no setup, por criarem um segundo sistema de pendências (issue\n"
        "  tracker), por serem específicas de TypeScript ou por estarem em `in-progress/`. Ver\n"
        "  `docs/ops/MATTPOCOCK-SKILLS.md`.\n"
        "- **Adaptações:** `git-guardrails-claude-code` (hook novo em Python: deixa o push normal e bloqueia\n"
        "  --force, push para main, rebase…), `wizard` (o `write_env` recusa `.env` que o git não ignora; regras\n"
        "  de segredos), `to-questionnaire` (grava fora do repo, nunca em `docs/knowledge/`).\n"
        "- **Scan:** `skill-scout scan` em cada skill adaptada: ver `docs/ops/MATTPOCOCK-SKILLS.md`.\n\n"
        "| Skill | Para quê | Adaptada | sha256 do SKILL.md (12) |\n|---|---|---|---|\n" + rows + "\n",
        encoding="utf-8",
    )


def install_script(commit: str) -> None:
    """O comando que o maestro corre (o skill-scout recusa aprovações de agentes de IA).

    Os hashes vêm do próprio skill-scout sobre o conteúdo adaptado: se o vendor mudar e o script não for
    regenerado, o hash não bate e nada é instalado (fail-closed).
    """
    sys.path.insert(0, str(ROOT / "oss" / "skill-scout" / "src"))
    from skill_scout.treehash import tree_hash

    lines = [
        "#!/bin/sh",
        f"# Instala {len(SELECTED)} skills de mattpocock/skills (adaptadas) no Claude Code de um repo.",
        "# Gerado por scripts/vendor_mattpocock_skills.py; não editar à mão.",
        f"# Origem: {UPSTREAM}@{commit} (MIT). Adaptações em vendor/mattpocock-skills/PROVENANCE.md.",
        "#",
        "# Corre TU, no teu terminal: o skill-scout recusa aprovações vindas de um agente de IA.",
        "# Ao correr isto aprovas o conteúdo pelos hashes abaixo.",
        "#   pip install -e oss/skill-scout            # uma vez",
        "#   sh scripts/install-mattpocock-skills.sh .                     # neste repo (network-agents-setup)",
        "#   sh scripts/install-mattpocock-skills.sh ../agent-network-mcp  # ou noutro",
        "# Depois, no repo de destino: commit de .claude/skills/, skill-scout.lock.json e skill-scout.audit.jsonl.",
        "# O hook do git-guardrails só fica activo depois do passo 3 da skill (settings.json): pede-o ao Claude.",
        "set -eu",
        'NAS="$(cd "$(dirname "$0")/.." && pwd)"',
        'DEST="${1:?uso: sh scripts/install-mattpocock-skills.sh <caminho do repo de destino>}"',
        'cd "$DEST"',
        'one() { skill-scout install "$NAS/vendor/mattpocock-skills/skills/$1" --dest .claude/skills --approve-sha256 "$2"; }',
    ]
    for skill in sorted(p for p in (VENDOR / "skills").iterdir() if p.is_dir()):
        lines.append(f"one {skill.name} {tree_hash(skill).digest}")
    lines += [
        "skill-scout verify",
        f'echo "ok: {len(SELECTED)} skills de mattpocock/skills instaladas em $DEST/.claude/skills"',
        "",
    ]
    out = ROOT / "scripts" / "install-mattpocock-skills.sh"
    out.write_text("\n".join(lines), encoding="utf-8")
    out.chmod(0o755)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", required=True, type=Path, help="checkout de mattpocock/skills")
    ap.add_argument("--commit", required=True, help="commit esperado do checkout (o auditado)")
    args = ap.parse_args(argv)
    head = _git_head(args.src)
    if not head.startswith(args.commit):
        raise SystemExit(f"o checkout está em {head}, não em {args.commit}")
    digests = vendor(args.src)
    provenance(head, digests)
    install_script(head)
    print(f"ok: {len(digests)} skills em {VENDOR.relative_to(ROOT)}; instalador em scripts/install-mattpocock-skills.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
