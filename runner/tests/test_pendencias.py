"""H-01 (maestro, 2026-10-25): as contagens do PENDENCIAS.md vêm das tabelas, não de quem escreve.

Se falhar: `cd runner && python -m plan_runner.pendencias --fix` (só reescreve as contagens).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from plan_runner import pendencias as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE = (REPO_ROOT / pd.LIVE_FILE).read_text(encoding="utf-8")
HIST = (REPO_ROOT / pd.HIST_FILE).read_text(encoding="utf-8")


def test_contagens_do_repo_estao_certas() -> None:
    assert pd.fix(LIVE, HIST) == (LIVE, HIST), "corre: cd runner && python -m plan_runner.pendencias --fix"


def test_cada_linha_do_quadro_tem_estado_dono_e_sev_validos() -> None:
    items = pd.live_items(LIVE)
    assert items, "a tabela §4 ficou vazia ou mudou de formato"
    assert len({c[0] for c in items}) == len(items), "ID repetido no §4"


def test_mudar_um_estado_actualiza_cabecalho_e_resumos() -> None:
    row = next(line for line in LIVE.splitlines() if line.startswith("| ") and " | ABERTO | " in line)
    live, _ = pd.fix(LIVE.replace(row, row.replace(" | ABERTO | ", " | EM CURSO | ", 1)), HIST)
    before, after = pd.stats(LIVE, HIST)["by_state"], pd.stats(live, HIST)["by_state"]
    assert after["ABERTO"] == before["ABERTO"] - 1 and after["EM CURSO"] == before["EM CURSO"] + 1
    assert f"ABERTO {after['ABERTO']}, EM CURSO {after['EM CURSO']}" in live
    assert f"**Por estado:** ABERTO {after['ABERTO']} · EM CURSO {after['EM CURSO']}" in live


def test_fechar_um_item_conta_no_historico() -> None:
    row = next(line for line in LIVE.splitlines() if line.startswith("| ") and " | ABERTO | " in line)
    anchor = "|---|---|---|---|---|---|\n"
    hist = HIST.replace(anchor, anchor + "| X-1 | teste | 2026-10-25 | PR #0 | FECHADO | — |\n", 1)
    live, hist = pd.fix(LIVE.replace(row + "\n", ""), hist)
    s = pd.stats(live, hist)
    assert f"## 4. Tabela única ({len(s['items'])} itens vivos)" in live
    assert f"{s['history']} linhas: {s['finals']['FECHADO']} FECHADO" in hist


def test_estado_desconhecido_falha_fechado() -> None:
    row = next(line for line in LIVE.splitlines() if line.startswith("| ") and " | ABERTO | " in line)
    with pytest.raises(ValueError, match="estado `FEITO` desconhecido"):
        pd.stats(LIVE.replace(row, row.replace(" | ABERTO | ", " | FEITO | ", 1)), HIST)
