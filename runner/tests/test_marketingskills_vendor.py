"""Garde do vendor de coreyhaines31/marketingskills (scripts/vendor_marketingskills.py).

Sem parceiros pagos nem chamadas a APIs no que é incorporado, e cada skill nova do runner ligada
(skill + agente + capability + área). Não precisa de rede nem do checkout upstream.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
VENDOR = REPO_ROOT / "vendor" / "marketingskills"


def _script():
    spec = importlib.util.spec_from_file_location("vendor_marketingskills", REPO_ROOT / "scripts" / "vendor_marketingskills.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_vendor_tem_as_50_skills_e_licenca():
    mod = _script()
    names = {p.name for p in (VENDOR / "skills").iterdir() if p.is_dir()}
    assert names == set(mod.NEW) | set(mod.OVERLAP) and len(names) == 50
    assert "MIT License" in (VENDOR / "LICENSE").read_text(encoding="utf-8")
    prov = (VENDOR / "PROVENANCE.md").read_text(encoding="utf-8")
    assert re.search(r"\*\*Commit:\*\* `[0-9a-f]{40}`", prov)
    assert not list(VENDOR.rglob("evals"))


def test_nada_de_parceiros_pagos_nem_chamadas_a_api():
    mod = _script()
    # o PROVENANCE.md nomeia de propósito o que ficou de fora; tudo o resto não pode
    files = [
        p for p in VENDOR.rglob("*") if p.is_file() and p.suffix in (".md", ".html", ".csv") and p.name != "PROVENANCE.md"
    ]
    files += [REPO_ROOT / "skills" / "marketing" / n.replace("-", "_") / "SKILL.md" for n in mod.NEW]
    hits = [str(p.relative_to(REPO_ROOT)) for p in files if mod.FORBIDDEN.search(p.read_text(encoding="utf-8"))]
    assert not hits, hits
    assert not (VENDOR / "tools").exists()  # tools/ (CLIs, guias de API, parceiros) nunca entra


def test_cada_skill_nova_esta_ligada_no_runner():
    mod = _script()
    caps = yaml.safe_load((REPO_ROOT / "config" / "marketing-capabilities.yaml").read_text(encoding="utf-8"))
    by_action = {c["action"]: c for c in caps["capabilities"] if c.get("action")}
    areas = yaml.safe_load((REPO_ROOT / "config" / "areas.yaml").read_text(encoding="utf-8"))
    marketing = next(a for a in areas["areas"] if a["id"] == "marketing")
    for name in mod.NEW:
        action = name.replace("-", "_")
        skill = REPO_ROOT / "skills" / "marketing" / action / "SKILL.md"
        agent = REPO_ROOT / "agents" / "marketing" / f"{action}.agent.md"
        assert skill.exists() and agent.exists(), action
        assert "## Contrato do runner (obrigatório)" in skill.read_text(encoding="utf-8")
        cap = by_action[action]
        assert cap["agent"] == f"marketing.{action}" and cap["status"] in ("partial", "implemented")
        assert f"marketing.{action}" in marketing["agents"]


def test_conformidade_nas_skills_de_contacto():
    for action in ("cold_email", "prospecting", "sms"):
        text = (REPO_ROOT / "skills" / "marketing" / action / "SKILL.md").read_text(encoding="utf-8")
        assert "RGPD" in text and "LGPD" in text, action
