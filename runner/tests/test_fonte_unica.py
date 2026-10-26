"""H-01, opção B (maestro, 2026-10-25): o passado vive num só sítio.

Os documentos antigos saíram da árvore; a ficha de cada um e o link permanente para o texto
integral estão no §13 do docs/initiatives/PENDENCIAS-HISTORICO.md. Estes testes falham se:
  - voltar a existir docs/archive/ ou uma referência a um ficheiro lá dentro;
  - um link para um documento antigo apontar para outro commit que não os fixados no §13;
  - o §13 deixar de ter a ficha de um documento antigo;
  - um link relativo nos documentos vivos (docs/, README, CLAUDE.md) estiver partido.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HIST = REPO_ROOT / "docs/initiatives/PENDENCIAS-HISTORICO.md"
NAS = "https://github.com/souzalrns/network-agents-setup/blob/"
MCP = "https://github.com/souzalrns/agent-network-mcp/blob/"
# e7a29ae: base das siglas P:/O:/ST: (linhas exactas); a5efdbe: última versão antes do arquivo.
NAS_SHAS = {"e7a29aea36cff52e0e4575c6e7c6de44815d4039", "a5efdbe4e533050045f0af4c9df8032c2bb8775a"}
MCP_SHA = "9803caaa764c897e055bc1b9c5e0fdd168ae922a"
OLD_NAS = (
    "docs/initiatives/STATUS.md", "docs/ops/PROGRESS-SESSAO.md", "docs/audit/PLANO-DE-ACAO.md",
    "docs/initiatives/OPEN-ITEMS.md", "docs/initiatives/PENDENCIAS_T6.md", "docs/ops/PENDENCIAS-CRUZADAS.md",
    "docs/architecture/MASTER-PLAN.md", "docs/STATUS.md", "docs/STATUS-ECOSSISTEMA.md", "docs/STATUS-PROJETOS.md",
)
OLD_MCP = (
    "docs/PLANO_REESTRUTURACAO_AGENT_NETWORK.md", "docs/PLANO_REESTRUTURACAO_AGENT_NETWORK_v1.1.md",
    "docs/PLANO_REESTRUTURACAO_AGENT_NETWORK_v1.2.md", "docs/ADDENDUM_PADROES_ORQUESTRADORES.md",
    "docs/ops/diagnostico-vm-2026.txt",
)
IMPORTED = (
    "marketing-base.md", "produto-tech-a11y-seo.md", "arquitetura-agentes-planejamento-rede-docs.md",
    "comunicacoes-atendimento-base.md", "guia-tdd-testes.md", "radar-ferramentas-opensource.md",
    "revisor-codigo-security-database.md", "MANIFEST.md", "PADROES_ERROS_IA.md",
    "ADDENDUM_PADROES_ORQUESTRADORES.md", "README.md",
)
# Documentos antigos que já não existem na árvore (o docs/STATUS.md voltou a existir, refeito).
GONE_NAS = tuple(p for p in OLD_NAS if p != "docs/STATUS.md")


def _tracked() -> list[str]:
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("sem checkout git")
    out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return [f for f in out.stdout.splitlines() if not f.startswith(("vendor/", "oss/")) and "node_modules/" not in f]


def _texts() -> dict[str, str]:
    texts = {}
    for rel in _tracked():
        p = REPO_ROOT / rel
        if p.suffix.lower() not in {".md", ".py", ".ts", ".js", ".yaml", ".yml", ".json", ".txt", ".toml", ".sh"}:
            continue
        try:
            texts[rel] = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return texts


def test_nao_ha_docs_archive_nem_copias_do_mcp() -> None:
    assert not [f for f in _tracked() if f.startswith(("docs/archive/", "docs/knowledge/imported-from-production/"))]


def test_nenhuma_referencia_a_ficheiros_do_arquivo() -> None:
    bad = [f"{rel}: {m}" for rel, text in _texts().items()
           for m in re.findall(r"(?<![\w-])archive/[\w./-]+\.(?:md|txt)\b|\]\((?:\.\.?/)+archive/", text)]
    assert bad == [], "referências ao arquivo (usar o link do §13 do PENDENCIAS-HISTORICO.md):\n" + "\n".join(bad)


def test_links_para_documentos_antigos_usam_os_commits_fixados() -> None:
    gone = "|".join(re.escape(p) for p in GONE_NAS)
    bad = []
    for rel, text in _texts().items():
        for sha, path in re.findall(rf"{re.escape(NAS)}([0-9a-f]{{7,40}})/({gone})\b", text):
            if sha not in NAS_SHAS:
                bad.append(f"{rel}: {sha}/{path}")
    assert bad == [], "links para documentos antigos noutro commit:\n" + "\n".join(bad)


def test_paragrafo_13_tem_a_ficha_de_cada_documento_antigo() -> None:
    sec13 = HIST.read_text(encoding="utf-8").split("\n## 13.", 1)
    assert len(sec13) == 2, "falta o §13 (documentos antigos) no PENDENCIAS-HISTORICO.md"
    body = sec13[1]
    for path in OLD_NAS:
        assert f"`{path}" in body and f"a5efdbe4e533050045f0af4c9df8032c2bb8775a/{path})" in body, path
    for path in OLD_MCP:
        assert f"`{path}" in body and f"{MCP}{MCP_SHA}/{path})" in body, path
    for name in IMPORTED:
        assert f"imported-from-production/{name})" in body, name


def test_os_links_fixados_existem_nesses_commits() -> None:
    """Só corre com o histórico completo (o CI faz checkout raso; localmente corre sempre)."""
    text = "\n".join(_texts().values())
    pairs = set(re.findall(rf"{re.escape(NAS)}({'|'.join(NAS_SHAS)})/([\w./-]+?)(?:#L\d+)?\)", text))
    assert pairs, "nenhum link fixado encontrado"
    for sha in NAS_SHAS:
        ok = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=REPO_ROOT, capture_output=True)
        if ok.returncode != 0:
            pytest.skip("checkout raso: os commits fixados não estão disponíveis")
    missing = [f"{sha[:7]}:{path}" for sha, path in sorted(pairs)
               if subprocess.run(["git", "cat-file", "-e", f"{sha}:{path}"], cwd=REPO_ROOT,
                                 capture_output=True).returncode != 0]
    assert missing == [], "links fixados para ficheiros que não existem nesse commit:\n" + "\n".join(missing)


def test_links_relativos_dos_documentos_vivos_resolvem() -> None:
    files = [f for f in _tracked() if f.endswith(".md")
             and (f.startswith(("docs/", "skills/", ".claude/skills/")) or "/" not in f)]
    bad = []
    for rel in files:
        text = re.sub(r"```.*?```", "", (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace"), flags=re.S)
        for target in re.findall(r"\]\(([\w./%-]+)(?:#[\w%-]*)?\)", text):
            if not target.startswith("/") and not ((REPO_ROOT / rel).parent / target).exists():  # /x = caminho web de exemplo
                bad.append(f"{rel}: {target}")
    assert bad == [], "links relativos partidos:\n" + "\n".join(bad)


def test_indice_da_arquitectura_lista_tudo() -> None:
    """H-01: cada documento e cada pasta de docs/architecture/ entra no README (um índice que não mente)."""
    arch = REPO_ROOT / "docs" / "architecture"
    readme = (arch / "README.md").read_text(encoding="utf-8")
    items = [p.name for p in arch.glob("*.md") if p.name != "README.md"] + [p.name + "/" for p in arch.iterdir() if p.is_dir()]
    missing = [name for name in sorted(items) if f"](./{name})" not in readme]
    assert missing == [], f"falta no docs/architecture/README.md: {missing}"
