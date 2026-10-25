"""Inventário gerado: a única fonte das contagens do repo (H-01, decisão do maestro 2026-10-25).

Porquê: os READMEs e os índices diziam números escritos à mão (38 agentes, ~70 skills,
830+ testes) que ninguém actualizava. Aqui cada número sai dos ficheiros de config e de
agentes, e o docs/generated/INVENTORY.md é só o resultado. O teste
`test_inventory.py` falha se o ficheiro gerado ou os números citados nos documentos
divergirem do que este módulo conta.

Não conta testes: o número de testes muda com cada PR e sai do próprio pytest
(`python -m pytest --collect-only -q`); os documentos dizem um mínimo ("1000+").

OFFICE-MCP-SYNC: `--check-mcp` compara os ids de config/mcp-agents.yaml com os de
agent-network-mcp/lib/agents.js (repo público; lê o ficheiro em bruto, sem credenciais).

CLI:  cd runner && python -m plan_runner.inventory              (escreve docs/generated/INVENTORY.md)
      cd runner && python -m plan_runner.inventory --check      (sai 1 se o ficheiro estiver desactualizado)
      cd runner && python -m plan_runner.inventory --check-mcp [FICHEIRO]
                  (sem FICHEIRO lê o lib/agents.js do main do MCP; o URL é fixo, não vem da CLI)
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

from .areas import load_areas
from .office import load_mcp_agents, load_office

INVENTORY_FILE = Path("docs") / "generated" / "INVENTORY.md"
# A mesma regra do scripts/document-agents.js do MCP: chave de topo seguida de `id: "..."`.
_MCP_ID = re.compile(r"""\n\s*["']?([a-z0-9-]+)["']?\s*:\s*\{\s*\n\s*id:\s*["']([^"']+)["']""")
_NODE_ID = re.compile(r"""^\s*id:\s*['"]([^'"]+)['"]""", re.M)


def counts(repo_root: Path) -> dict[str, Any]:
    """Todas as contagens, calculadas a partir dos ficheiros. Sem rede e sem data."""
    areas = load_areas(repo_root)
    runtime = [a for area in areas for a in area.get("agents") or []]
    mcp = load_mcp_agents(repo_root)
    office = load_office(repo_root)
    depts = office.get("departments") or []
    seats = [s for d in depts for s in d.get("seats") or []]
    skills = sorted((repo_root / "skills").glob("**/SKILL.md"))
    node_cfg = repo_root / "config" / "agents.config.ts"
    return {
        "areas": len(areas),
        "runtime_agents": len(runtime),
        "agents_by_area": {a["id"]: len(a.get("agents") or []) for a in areas},
        "skills": len(skills),
        "skills_by_domain": dict(sorted(Counter(p.relative_to(repo_root / "skills").parts[0] for p in skills).items())),
        "plans": len(list((repo_root / "docs" / "orchestration").glob("**/*.plan.yaml"))),
        "mcp_agents": len(mcp),
        "mcp_also_runtime": sum(1 for a in mcp if a.get("runtime")),
        "mcp_only": sum(1 for a in mcp if not a.get("runtime")),
        "office_wings": len({d.get("wing") for d in depts}),
        "office_departments": len(depts),
        "office_seats": len(seats),
        "office_agents": sum(len(s.get("agents") or []) for s in seats),
        "node_agents": len(_NODE_ID.findall(node_cfg.read_text(encoding="utf-8"))) if node_cfg.exists() else 0,
    }


def render(c: dict[str, Any]) -> str:
    """Markdown determinístico (sem data), para o teste poder comparar byte a byte."""
    lines = [
        "# Inventário — contagens geradas",
        "",
        "> **Não editar à mão.** Regenerar com: `cd runner && python -m plan_runner.inventory`",
        "> O CI e `runner/tests/test_inventory.py` falham se este ficheiro ou os números citados",
        "> nos documentos divergirem dos ficheiros de config. Fonte: `runner/plan_runner/inventory.py`.",
        "",
        "## Resumo",
        "",
        "| O quê | Quantos | Fonte |",
        "|---|---:|---|",
        f"| Agentes do runner (`plan_runner`) | {c['runtime_agents']} | `config/areas.yaml` (validado contra `agents/**/*.agent.md`) |",
        f"| Áreas do router | {c['areas']} | `config/areas.yaml` |",
        f"| Skills | {c['skills']} | `skills/**/SKILL.md` |",
        f"| Planos de exemplo | {c['plans']} | `docs/orchestration/**/*.plan.yaml` |",
        f"| Agentes do MCP de produção | {c['mcp_agents']} | `config/mcp-agents.yaml` (cópia dos ids de `agent-network-mcp/lib/agents.js`) |",
        f"| … também no runner | {c['mcp_also_runtime']} | `runtime:` preenchido |",
        f"| … só no MCP | {c['mcp_only']} | `runtime: null` |",
        f"| Agentes no escritório (runner + só MCP) | {c['office_agents']} | `config/office.yaml` |",
        f"| Departamentos / alas / lugares do escritório | {c['office_departments']} / {c['office_wings']} / {c['office_seats']} | `config/office.yaml` |",
        f"| Agentes da plataforma Node (`apps/api`) | {c['node_agents']} | `config/agents.config.ts` (catálogo em `docs/generated/AGENTS.md`) |",
        "",
        "Testes: não se contam aqui (mudam a cada PR). `cd runner && python -m pytest --collect-only -q`.",
        "",
        "## Agentes do runner por área",
        "",
        "| Área | Agentes |",
        "|---|---:|",
        *[f"| `{area}` | {n} |" for area, n in c["agents_by_area"].items()],
        "",
        "## Skills por domínio",
        "",
        "| Domínio | Skills |",
        "|---|---:|",
        *[f"| `{dom}` | {n} |" for dom, n in c["skills_by_domain"].items()],
        "",
    ]
    return "\n".join(lines)


def mcp_ids_from_source(source: str) -> list[str]:
    """Ids dos agentes em lib/agents.js (sem executar JavaScript)."""
    seen: dict[str, None] = {}
    for _key, aid in _MCP_ID.findall(source):
        seen.setdefault(aid, None)
    return list(seen)


def mcp_sync_errors(repo_root: Path, source: str) -> list[str]:
    """Diferenças entre lib/agents.js e config/mcp-agents.yaml (OFFICE-MCP-SYNC)."""
    real = set(mcp_ids_from_source(source))
    if not real:
        return ["lib/agents.js: não encontrei nenhum agente (o formato mudou?)"]
    listed = {a.get("id") for a in load_mcp_agents(repo_root)}
    errors = [f"`{i}` está no MCP mas falta em config/mcp-agents.yaml (e no config/office.yaml)"
              for i in sorted(real - listed)]
    errors += [f"`{i}` está em config/mcp-agents.yaml mas já não existe no MCP" for i in sorted(listed - real)]
    return errors


def fetch_mcp_source() -> str:
    """lib/agents.js do main do agent-network-mcp (público). URL literal: nada vindo de fora."""
    resp = httpx.get("https://raw.githubusercontent.com/souzalrns/agent-network-mcp/main/lib/agents.js",
                     timeout=30, follow_redirects=False)
    resp.raise_for_status()
    return resp.text


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    repo_root = Path(__file__).resolve().parents[2]
    out = repo_root / INVENTORY_FILE
    if args[:1] == ["--check-mcp"]:
        where = args[1] if len(args) > 1 else "agent-network-mcp@main"
        source = Path(args[1]).read_text(encoding="utf-8") if len(args) > 1 else fetch_mcp_source()
        errors = mcp_sync_errors(repo_root, source)
        if errors:
            print(f"OFFICE-MCP-SYNC: {len(errors)} diferença(s) com {where}", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print(f"OFFICE-MCP-SYNC: OK ({len(load_mcp_agents(repo_root))} agentes iguais nos 2 repos)")
        return 0
    text = render(counts(repo_root))
    if args[:1] == ["--check"]:
        current = out.read_text(encoding="utf-8") if out.exists() else ""
        if current != text:
            print(f"{INVENTORY_FILE} desactualizado: corre `cd runner && python -m plan_runner.inventory`",
                  file=sys.stderr)
            return 1
        print(f"{INVENTORY_FILE}: actualizado")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"inventário: {out.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
