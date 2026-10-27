"""Prontidão da plataforma: a matriz das 8 capacidades críticas, gerada e verificada (Etapa 3, 2026-10-27).

A fonte é config/platform-readiness.yaml: para cada capacidade, os testes, os runs reais e os
IDs vivos do PENDENCIAS.md que a limitam. Este módulo verifica que cada prova existe (a função de
teste, o excerto no documento de evidência, o ID no §4) e calcula o estado. Ninguém escreve
"PROVADA" à mão: sem um run real citado e verificável, uma capacidade não passa de TESTADA.

CLI:  cd runner && python -m plan_runner.prontidao            (escreve docs/generated/PRONTIDAO.md)
      cd runner && python -m plan_runner.prontidao --check    (sai 1 se uma prova faltar ou o ficheiro divergir)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

from .pendencias import LIVE_FILE, live_items

CONFIG_FILE = Path("config") / "platform-readiness.yaml"
OUT_FILE = Path("docs") / "generated" / "PRONTIDAO.md"
TESTS_DIR = Path("runner") / "tests"
STATES = ("PROVADA", "TESTADA", "SEM PROVA")


def load(repo_root: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load((repo_root / CONFIG_FILE).read_text(encoding="utf-8")) or {}
    caps = data.get("capabilities")
    if not isinstance(caps, list) or not caps:
        raise ValueError(f"{CONFIG_FILE}: falta a lista `capabilities`")
    return caps


def state(cap: dict[str, Any]) -> str:
    if not cap.get("testes"):
        return "SEM PROVA"
    return "PROVADA" if cap.get("runs") else "TESTADA"


def errors(repo_root: Path, caps: list[dict[str, Any]]) -> list[str]:
    """Cada prova citada tem de existir. Devolve a lista de erros (vazia = tudo verificado)."""
    errs: list[str] = []
    live = {row[0]: row for row in live_items((repo_root / LIVE_FILE).read_text(encoding="utf-8"))}
    ids = [c.get("id") for c in caps]
    if len(ids) != len(set(ids)):
        errs.append("ids de capacidade repetidos")
    for cap in caps:
        cid = cap.get("id")
        for key in ("id", "name", "criterio"):
            if not cap.get(key):
                errs.append(f"{cid}: falta `{key}`")
        for ref in cap.get("testes") or []:
            path, _, func = str(ref).partition("::")
            f = repo_root / TESTS_DIR / path
            if not func or not f.is_file():
                errs.append(f"{cid}: teste `{ref}` não existe")
            elif not re.search(rf"^(?:async )?def {re.escape(func)}\(", f.read_text(encoding="utf-8"), re.M):
                errs.append(f"{cid}: a função `{func}` não está em {path}")
        for run in cap.get("runs") or []:
            doc = repo_root / str(run.get("doc", ""))
            if not doc.is_file():
                errs.append(f"{cid}: documento de evidência `{run.get('doc')}` não existe")
            elif str(run.get("anchor", "")) not in doc.read_text(encoding="utf-8"):
                errs.append(f"{cid}: o excerto `{run.get('anchor')}` não está em {run.get('doc')}")
        for item in cap.get("lacunas") or []:
            if item not in live:
                errs.append(f"{cid}: lacuna `{item}` não é um item vivo do §4 (fechou? tirar daqui)")
    return errs


def render(repo_root: Path, caps: list[dict[str, Any]]) -> str:
    live = {row[0]: row for row in live_items((repo_root / LIVE_FILE).read_text(encoding="utf-8"))}
    lines = [
        "# Prontidão da plataforma — gerado",
        "",
        "> **Não editar à mão.** Regenerar com: `cd runner && python -m plan_runner.prontidao`",
        "> Fonte: `config/platform-readiness.yaml`. O CI falha se uma prova citada deixar de existir.",
        "> **PROVADA** = testes + run real citado; **TESTADA** = só testes; **SEM PROVA** = nenhum teste.",
        "> As lacunas são itens vivos do `PENDENCIAS.md` (o estado deles vive lá, não aqui).",
        "",
        "| Capacidade | Critério de aceitação | Estado | Testes | Runs reais | Lacunas (PENDENCIAS) |",
        "|---|---|---|---:|---:|---|",
    ]
    for cap in caps:
        st = state(cap)
        lac = cap.get("lacunas") or []
        st_txt = f"**{st}**" + (", com lacunas" if lac and st != "SEM PROVA" else "")
        lac_txt = ", ".join(f"{i} ({live[i][3]}, {live[i][5]})" for i in lac if i in live) or "—"
        lines.append(f"| {cap['name']} | {cap['criterio']} | {st_txt} | {len(cap.get('testes') or [])} "
                     f"| {len(cap.get('runs') or [])} | {lac_txt} |")
    lines += ["", "## Provas por capacidade", ""]
    for cap in caps:
        lines += [f"### {cap['name']} — {state(cap)}", ""]
        lines += [f"- teste: `runner/tests/{t}`" for t in cap.get("testes") or []]
        lines += [f"- run real: `{r['doc']}` (\"{r['anchor']}\")" for r in cap.get("runs") or []]
        if not cap.get("runs"):
            lines.append("- run real: **nenhum** (só testes)")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[2]
    try:
        caps = load(root)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"prontidão: {e}", file=sys.stderr)
        return 1
    errs = errors(root, caps)
    if errs:
        print(f"prontidão: {len(errs)} prova(s) em falta", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    text = render(root, caps)
    out = root / OUT_FILE
    if args[:1] == ["--check"]:
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            print(f"{OUT_FILE} desactualizado: cd runner && python -m plan_runner.prontidao", file=sys.stderr)
            return 1
        print(f"prontidão: OK ({len(caps)} capacidades, todas as provas verificadas)")
        return 0
    out.write_text(text, encoding="utf-8")
    print(f"prontidão: {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
