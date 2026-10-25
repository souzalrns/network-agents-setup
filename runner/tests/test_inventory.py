"""H-01 (maestro, 2026-10-25): os números dos documentos vêm do inventário gerado.

Se um teste daqui falhar: `cd runner && python -m plan_runner.inventory` e corrige o número
citado no documento que o teste indicar. Nunca o contrário (escrever o número à mão).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from plan_runner import inventory as inv

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def c() -> dict:
    return inv.counts(REPO_ROOT)


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _claims(pattern: str, text: str) -> set[int]:
    found = {int(m) for m in re.findall(pattern, text)}
    assert found, f"o documento deixou de citar o número ({pattern})"
    return found


def test_inventario_gerado_esta_actualizado(c) -> None:
    assert _read(str(inv.INVENTORY_FILE)) == inv.render(c), \
        "docs/generated/INVENTORY.md desactualizado: cd runner && python -m plan_runner.inventory"


def test_escritorio_tem_todos_os_agentes_uma_vez(c) -> None:
    assert c["office_agents"] == c["runtime_agents"] + c["mcp_only"]
    assert c["mcp_agents"] == c["mcp_also_runtime"] + c["mcp_only"]


def test_readme_cita_os_numeros_reais(c) -> None:
    readme = _read("README.md")
    assert _claims(r"(\d+) runtime agents", readme) == {c["runtime_agents"]}
    assert _claims(r"(\d+) skills \(Markdown\)", readme) == {c["skills"]}


def test_office_md_cita_os_numeros_reais(c) -> None:
    m = re.search(r"\*\*Hoje:\*\* (\d+) agentes \((\d+) do runner \+ (\d+) só do MCP de produção\), "
                  r"(\d+) departamentos em (\d+) alas, (\d+) lugares", _read("docs/ops/OFFICE.md"))
    assert m, "docs/ops/OFFICE.md deixou de dizer os números do escritório"
    assert tuple(map(int, m.groups())) == (c["office_agents"], c["runtime_agents"], c["mcp_only"],
                                           c["office_departments"], c["office_wings"], c["office_seats"])


def test_portfolio_cita_os_numeros_reais(c) -> None:
    m = re.search(r"\*\*(\d+)\*\* agentes do runner · \*\*(\d+)\*\* skills · \*\*(\d+)\*\* planos",
                  _read("docs/PORTFOLIO.md"))
    assert m, "docs/PORTFOLIO.md deixou de dizer os números do inventário"
    assert tuple(map(int, m.groups())) == (c["runtime_agents"], c["skills"], c["plans"])


@pytest.mark.parametrize("rel, key", [
    ("docs/generated/SKILLS.md", "skills"),
    ("docs/generated/AGENTS.md", "node_agents"),
])
def test_catalogos_gerados_batem_com_o_inventario(c, rel, key) -> None:
    assert _claims(r"Total: \*\*(\d+)\*\*", _read(rel)) == {c[key]}, \
        f"{rel} desactualizado (regenerar com o comando no topo do ficheiro)"


# --- OFFICE-MCP-SYNC (sem rede: o CI corre --check-mcp contra o repo do MCP) ---

JS = '''export const AGENTS = {
  mesaflow: {
    id: "mesaflow",
    description:
      "Backend " +
      "NestJS",
  },
  "vianna-gestao": {
    id: "vianna-gestao",
    description: "x",
  },
};
'''


def test_le_os_ids_do_lib_agents_js() -> None:
    assert inv.mcp_ids_from_source(JS) == ["mesaflow", "vianna-gestao"]


def test_sync_aponta_as_diferencas_nos_dois_sentidos() -> None:
    errors = inv.mcp_sync_errors(REPO_ROOT, JS)
    assert any("está em config/mcp-agents.yaml mas já não existe no MCP" in e for e in errors)
    novo = JS.replace("};\n", '  "agente-novo": {\n    id: "agente-novo",\n  },\n};\n')
    assert any("`agente-novo` está no MCP mas falta" in e for e in inv.mcp_sync_errors(REPO_ROOT, novo))


def test_sync_falha_fechado_se_o_formato_mudar() -> None:
    assert inv.mcp_sync_errors(REPO_ROOT, "module.exports = []") == [
        "lib/agents.js: não encontrei nenhum agente (o formato mudou?)"]


def test_sync_ok_com_a_lista_actual() -> None:
    ids = [a["id"] for a in inv.load_mcp_agents(REPO_ROOT)]
    js = "export const AGENTS = {" + "".join(f'\n  "{i}": {{\n    id: "{i}",\n  }},' for i in ids) + "\n};\n"
    assert inv.mcp_sync_errors(REPO_ROOT, js) == []


def test_cli_check_e_check_mcp(tmp_path, capsys) -> None:
    assert inv.main(["--check"]) == 0
    src = tmp_path / "agents.js"
    src.write_text(JS, encoding="utf-8")
    assert inv.main(["--check-mcp", str(src)]) == 1
    assert "OFFICE-MCP-SYNC" in capsys.readouterr().err
