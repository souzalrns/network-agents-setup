"""GOV-IMPACT-1: separação repo público / privado (docs/governance/PRIVACY-POLICY.md §1–§2).

- público: nenhum ficheiro de cliente versionado (`memory/<cliente>/...`) e a regra no .gitignore;
- privado: `privacy_contact` é um e-mail (o titular tem de ter a quem pedir);
- a política cobre as secções exigidas e cita as tabelas onde os dados vivem.
Sem rede, sem BD; usa `git ls-files` (o CI faz checkout do repo).
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT = REPO_ROOT / "config/deployment.yaml"
POLICY = REPO_ROOT / "docs/governance/PRIVACY-POLICY.md"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
CLIENT_DATA = re.compile(r"^memory/[^/]+/")  # memory/<client_id>/... (working memory, S30)


@pytest.fixture(scope="module")
def deployment():
    data = yaml.safe_load(DEPLOYMENT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _tracked() -> list[str]:
    if shutil.which("git") is None or not (REPO_ROOT / ".git").exists():
        pytest.skip("sem git/checkout")
    out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)  # noqa: S603,S607
    return out.stdout.splitlines()


def test_visibilidade_declarada(deployment):
    assert deployment.get("repo_visibility") in ("public", "private")


def test_repo_publico_nao_versiona_dados_de_clientes(deployment):
    if deployment["repo_visibility"] != "public":
        pytest.skip("repo privado: os dados de clientes podem existir (fora do git, recomendado)")
    leaked = [p for p in _tracked() if CLIENT_DATA.match(p)]
    assert not leaked, f"dados de cliente versionados num repo público: {leaked}"
    assert "/memory/*/" in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_repo_privado_exige_contacto_de_privacidade(deployment):
    contact = deployment.get("privacy_contact")
    if deployment["repo_visibility"] == "private":
        assert isinstance(contact, str) and EMAIL.match(contact), "privacy_contact obrigatório num repo privado"
    elif contact is not None:
        assert isinstance(contact, str) and EMAIL.match(contact), "privacy_contact, se existir, tem de ser um e-mail"


def test_politica_cobre_as_seccoes_exigidas():
    text = POLICY.read_text(encoding="utf-8")
    for heading in (
        "## 1. Responsável pelo tratamento e contacto",
        "## 2. Repositório público vs. repositório privado",
        "## 3. Que dados são tratados",
        "## 4. Onde estão",
        "## 5. Finalidades e bases legais",
        "## 7. Retenção",
        "## 8. Direitos do titular e como exercê-los",
        "## 9. Sub-processadores",
        "## 10. Transferências internacionais",
        "## 11. Segurança",
        "## 13. Alterações a esta política",
    ):
        assert heading in text, heading
    assert re.search(r"\*\*Em vigor desde:\*\* \d{4}-\d{2}-\d{2}", text)
    assert "enquanto durar o contrato + 90 dias" in text


def test_politica_cita_as_tabelas_do_runner():
    """As tabelas que o próprio NAS cria/usa têm de estar no inventário da política."""
    text = POLICY.read_text(encoding="utf-8")
    sql = (REPO_ROOT / "scripts/create_memory_l4_table.sql").read_text(encoding="utf-8")
    assert "memory_l4" in sql
    for table in ("memory_l4", "token_usage", "knowledge_chunks", "agent_log", "project_state"):
        assert f"`{table}`" in text, table
