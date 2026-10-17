"""Guarda do vendor de mattpocock/skills (scripts/vendor_mattpocock_skills.py), sem rede nem checkout upstream.

As 6 skills escolhidas e mais nenhuma, a licença e a proveniência, o instalador com os hashes do conteúdo
adaptado (fail-closed), e as adaptações que importam: o hook do git-guardrails deixa o push normal e bloqueia
o que as regras do maestro proíbem; o wizard recusa escrever segredos num ficheiro que o git não ignora.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VENDOR = REPO_ROOT / "vendor" / "mattpocock-skills"
HOOK = VENDOR / "skills" / "git-guardrails-claude-code" / "scripts" / "block-dangerous-git.py"
TEMPLATE = VENDOR / "skills" / "wizard" / "template.sh"


def _script():
    spec = importlib.util.spec_from_file_location("vendor_mattpocock_skills", REPO_ROOT / "scripts" / "vendor_mattpocock_skills.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_so_as_6_skills_escolhidas_com_licenca_e_proveniencia():
    mod = _script()
    names = {p.name for p in (VENDOR / "skills").iterdir() if p.is_dir()}
    assert names == set(mod.SELECTED) and len(names) == 6
    assert "MIT License" in (VENDOR / "LICENSE").read_text(encoding="utf-8")
    assert re.search(r"\*\*Commit:\*\* `[0-9a-f]{40}`", (VENDOR / "PROVENANCE.md").read_text(encoding="utf-8"))
    assert not (VENDOR / "skills" / "git-guardrails-claude-code" / "scripts" / "block-dangerous-git.sh").exists()


def test_instalador_aprova_exactamente_o_conteudo_do_vendor():
    sys.path.insert(0, str(REPO_ROOT / "oss" / "skill-scout" / "src"))
    from skill_scout.treehash import tree_hash

    script = (REPO_ROOT / "scripts" / "install-mattpocock-skills.sh").read_text(encoding="utf-8")
    pins = dict(re.findall(r"^one (\S+) ([0-9a-f]{64})$", script, re.M))
    assert set(pins) == {p.name for p in (VENDOR / "skills").iterdir() if p.is_dir()}
    for name, digest in pins.items():
        assert tree_hash(VENDOR / "skills" / name).digest == digest, f"{name}: regenerar o vendor"
    assert "skill-scout verify" in script


def _hook(command: str, cwd: Path | None = None) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    # fixed argv: this interpreter running the vendored hook
    return subprocess.run([sys.executable, str(HOOK)], input=payload, text=True, capture_output=True, cwd=cwd).returncode  # nosemgrep


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin feat/x",
        "git push -fu origin feat/x",
        "git push --force-with-lease",
        "git push origin +feat/x",
        "git push origin main",
        "git push origin feat/x:master",
        "git push origin :feat/x",
        "cd x && git rebase main",
        "git -C /tmp reset --hard HEAD~1",
        "git clean -fdx",
        "git branch -D old",
        "git checkout .",
        "git restore .",
        "git filter-repo --path x",
    ],
)
def test_hook_bloqueia_o_que_as_regras_proibem(command):
    assert _hook(command) == 2


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin feat/x",
        "git push origin HEAD:refs/heads/feat/x",
        "git reset --soft HEAD~1",
        "git clean -n",
        "git branch -d old",
        "git checkout feat/x",
        "echo 'git push --force'",
        "git commit -m 'git rebase later'",
        "ls | grep git",
    ],
)
def test_hook_deixa_o_fluxo_normal_de_prs(command, tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "feat/x"], cwd=tmp_path, check=True)
    assert _hook(command, cwd=tmp_path) == 0


def test_hook_bloqueia_push_sem_destino_estando_em_main(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    assert _hook("git push", cwd=tmp_path) == 2
    assert _hook("git push -u origin feat/x", cwd=tmp_path) == 0


def _write_env(tmp_path: Path) -> subprocess.CompletedProcess:
    lib = TEMPLATE.read_text(encoding="utf-8").split("run_wizard() {")[0]
    (tmp_path / "lib.sh").write_text(lib, encoding="utf-8")
    (tmp_path / "t.sh").write_text('. ./lib.sh\nwrite_env FOO "s3cr3t"\necho continued\n', encoding="utf-8")
    return subprocess.run(["bash", "t.sh"], cwd=tmp_path, text=True, capture_output=True)


def test_wizard_recusa_env_que_o_git_nao_ignora(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    r = _write_env(tmp_path)
    assert r.returncode != 0 and "continued" not in r.stdout
    assert not (tmp_path / ".env").exists()


def test_wizard_escreve_env_ignorado_com_modo_600(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    r = _write_env(tmp_path)
    assert r.returncode == 0 and "continued" in r.stdout
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "FOO='s3cr3t'\n"
    assert (tmp_path / ".env").stat().st_mode & 0o777 == 0o600


def test_questionario_nunca_vai_para_o_rag():
    text = (VENDOR / "skills" / "to-questionnaire" / "SKILL.md").read_text(encoding="utf-8")
    assert "in the current directory" not in text
    assert "docs/knowledge/" in text and "never commit it" in text
