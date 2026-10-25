"""Contagens do PENDENCIAS.md calculadas a partir das tabelas (H-01, maestro 2026-10-25).

Porquê: o cabeçalho, os títulos e os resumos §5/§6 eram recontados à mão a cada fecho e
ficavam errados. Aqui a fonte é a tabela §4 (itens vivos) e as tabelas §7, §8 e §10 do
PENDENCIAS-HISTORICO.md; o resto é derivado. `--fix` reescreve só as linhas de contagem,
nunca o conteúdo das linhas da tabela.

CLI:  cd runner && python -m plan_runner.pendencias          (sai 1 se alguma contagem estiver errada)
      cd runner && python -m plan_runner.pendencias --fix    (corrige as contagens nos 2 ficheiros)
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

LIVE_FILE = Path("docs") / "initiatives" / "PENDENCIAS.md"
HIST_FILE = Path("docs") / "initiatives" / "PENDENCIAS-HISTORICO.md"
STATES = ("ABERTO", "EM CURSO", "BLOQUEADO")
OWNERS = ("CLAUDE", "DEV", "AMBOS")
SEVERITIES = ("Crítica", "Alta", "Média", "Baixa")
FINAL_STATES = ("FECHADO", "OBSOLETO")


def _section(text: str, start: str, end: str) -> str:
    """Texto entre o título `start` e o próximo título `end` (exclusivo)."""
    _, found, rest = text.partition(start)
    if not found:
        raise ValueError(f"falta a secção `{start.strip()}`")
    return rest.split(end, 1)[0]


def _rows(block: str, ncols: int) -> list[list[str]]:
    out = []
    for line in block.splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == ncols and not set(cells[0]) <= set("-") and cells[0] not in ("ID", "#"):
            out.append(cells)
    return out


def live_items(live: str) -> list[list[str]]:
    """Linhas da tabela §4 (10 colunas). O §4.1 (detalhe do H-01) não conta."""
    block = _section(live, "\n## 4.", "\n## 5.").split("\n### ", 1)[0]
    return _rows(block, 10)


def stats(live: str, hist: str) -> dict:
    items = live_items(live)
    errors = [f"§4 `{c[0]}`: {name} `{c[i]}` desconhecido"
              for c in items for i, name, ok in ((3, "estado", STATES), (4, "dono", OWNERS), (5, "sev", SEVERITIES))
              if c[i] not in ok]
    if errors:
        raise ValueError("; ".join(errors))
    history = _rows(_section(hist, "\n## 7.", "\n## 8."), 6)
    finals = Counter(c[4] for c in history)
    unknown = set(finals) - set(FINAL_STATES)
    if unknown:
        raise ValueError(f"§7 do histórico: estado final desconhecido {sorted(unknown)}")
    return {
        "items": items,
        "by_state": Counter(c[3] for c in items),
        "history": len(history),
        "finals": finals,
        "contradictions": sum(1 for c in _rows(_section(hist, "\n## 8.", "\n## 10."), 5) if c[0].startswith("V")),
        "decided": sum(1 for c in _rows(_section(hist, "\n## 10.", "\n## 11."), 6) if c[0].startswith("P-")),
        "pending": sum(1 for c in _rows(_section(live, "\n## 10.", "\n## 11."), 6) if c[0].startswith("P-")),
    }


def _sub(pattern: str, repl: str, text: str, where: str) -> str:
    new, n = re.subn(pattern, lambda _m: repl, text, flags=re.M)
    if n != 1:
        raise ValueError(f"{where}: esperava 1 ocorrência de /{pattern}/, encontrei {n}")
    return new


def fix(live: str, hist: str) -> tuple[str, str]:
    """As duas versões com as contagens certas (o resto do texto fica igual)."""
    s = stats(live, hist)
    items, st, fin = s["items"], s["by_state"], s["finals"]
    states = ", ".join(f"{k} {st[k]}" for k in STATES)
    title7 = f"## 7. Histórico ({s['history']} linhas: {fin['FECHADO']} FECHADO, {fin['OBSOLETO']} OBSOLETO)"
    title8 = f"## 8. Contradições resolvidas ({s['contradictions']})"
    header = (
        "> **Contagens** (geradas: `cd runner && python -m plan_runner.pendencias --fix`; o CI falha se divergirem):\n"
        f"> - **{len(items)} itens vivos** (§4): {states};\n"
        f"> - **{s['history']} linhas de histórico** (no histórico, §7): {fin['FECHADO']} fechadas, {fin['OBSOLETO']} obsoletas;\n"
        f"> - **{s['contradictions']} contradições resolvidas** (no histórico, §8);\n"
        f"> - **{s['decided'] + s['pending']} decisões** A/B/C: {s['decided']} tomadas (no histórico, §10) e "
        f"**{s['pending']} por decidir** (§10 abaixo).\n"
    )
    live = _sub(r"^> \*\*Contagens\*\*.*\n(?:^> - .*\n){4}", header, live, "cabeçalho")
    live = _sub(r"^## 4\. Tabela única \(\d+ itens vivos\)$", f"## 4. Tabela única ({len(items)} itens vivos)", live, "§4")
    for owner in OWNERS:
        ids = [c[0] for c in items if c[4] == owner]
        live = _sub(rf"^\| {owner} \| \d+ \| .*$", f"| {owner} | {len(ids)} | {', '.join(ids)} |", live, f"§5 {owner}")
    for sev in SEVERITIES:
        ids = [c[0] for c in items if c[5] == sev]
        live = _sub(rf"^\| {sev} \| \d+ \| .*$", f"| {sev} | {len(ids)} | {', '.join(ids)} |", live, f"§6 {sev}")
    live = _sub(r"^\*\*Por estado:\*\* .*$", "**Por estado:** " + " · ".join(f"{k} {st[k]}" for k in STATES) + ".",
                live, "§6 por estado")
    unverified = [c[0] for c in items if c[9] == "NÃO VERIFICADO"]
    live = _sub(r"^\*\*NÃO VERIFICADO \(\d+\):\*\* .*$",
                f"**NÃO VERIFICADO ({len(unverified)}):** {', '.join(unverified) or '—'}.", live, "§6 não verificado")
    live = _sub(r"^> As \d+ decisões já tomadas", f"> As {s['decided']} decisões já tomadas", live, "§10")
    live = _sub(r"^## 7\. Histórico \(.*\)$", title7, live, "§7")
    live = _sub(r"^## 8\. Contradições resolvidas \(\d+\)$", title8, live, "§8")
    hist = _sub(r"^## 7\. Histórico \(.*\)$", title7, hist, "histórico §7")
    hist = _sub(r"^## 8\. Contradições resolvidas \(\d+\)$", title8, hist, "histórico §8")
    return live, hist


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[2]
    live_p, hist_p = root / LIVE_FILE, root / HIST_FILE
    live, hist = live_p.read_text(encoding="utf-8"), hist_p.read_text(encoding="utf-8")
    try:
        new_live, new_hist = fix(live, hist)
    except ValueError as e:
        print(f"PENDENCIAS: {e}", file=sys.stderr)
        return 1
    if args[:1] == ["--fix"]:
        live_p.write_text(new_live, encoding="utf-8")
        hist_p.write_text(new_hist, encoding="utf-8")
        print("PENDENCIAS: contagens escritas")
        return 0
    if (new_live, new_hist) != (live, hist):
        print("PENDENCIAS: contagens desactualizadas; corre `cd runner && python -m plan_runner.pendencias --fix`",
              file=sys.stderr)
        return 1
    n = len(live_items(live))
    print(f"PENDENCIAS: contagens OK ({n} itens vivos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
