"""ISO/IEC 42001 (P-40): o mapeamento em docs/governance/ não pode apodrecer em silêncio.

Ao estilo do test_knowledge_coverage: sem BD, sem rede. Verifica contra o repo:
- as 27 cláusulas 4–10 e os 38 controlos do Anexo A estão todos lá, uma só vez;
- estados válidos (N/A proibido nas cláusulas; `Aplicável: Não` ⇔ `N/A` com justificação);
- cada evidência existe (e o símbolo depois de `::` aparece no ficheiro);
- cada `Parcial`/`Falta` aponta para um item VIVO do PENDENCIAS §4;
- o resumo bate com as tabelas.
As evidências `ANM:` só se verificam com o clone do agent-network-mcp ao lado
(ou em ANM_REPO_ROOT); no CI do NAS esse teste fica `skipped`.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MAPPING = REPO_ROOT / "docs/governance/ISO-42001-MAPPING.md"
POLICY = REPO_ROOT / "docs/governance/AI-MANAGEMENT-SYSTEM.md"
PENDENCIAS = REPO_ROOT / "docs/initiatives/PENDENCIAS.md"

CLAUSES = (
    "4.1 4.2 4.3 4.4 5.1 5.2 5.3 6.1.1 6.1.2 6.1.3 6.1.4 6.2 6.3 "
    "7.1 7.2 7.3 7.4 7.5 8.1 8.2 8.3 8.4 9.1 9.2 9.3 10.1 10.2"
).split()
ANNEX_A = (
    "A.2.2 A.2.3 A.2.4 A.3.2 A.3.3 A.4.2 A.4.3 A.4.4 A.4.5 A.4.6 "
    "A.5.2 A.5.3 A.5.4 A.5.5 "
    "A.6.1.2 A.6.1.3 A.6.2.2 A.6.2.3 A.6.2.4 A.6.2.5 A.6.2.6 A.6.2.7 A.6.2.8 "
    "A.7.2 A.7.3 A.7.4 A.7.5 A.7.6 A.8.2 A.8.3 A.8.4 A.8.5 "
    "A.9.2 A.9.3 A.9.4 A.10.2 A.10.3 A.10.4"
).split()
STATES = ("Cumpre", "Parcial", "Falta", "N/A")
EVIDENCE = re.compile(r"^(?P<anm>ANM:)?(?P<path>[\w.\-/]+)(?:::(?P<sym>.+))?$")
FILE_LIKE = re.compile(r"(/|\.(md|py|ya?ml|json|js|ts|sql)$)")


def _table(text: str, heading: str) -> list[list[str]]:
    part = text.split("\n" + heading, 1)[1].split("\n## ", 1)[0]  # só o cabeçalho, não uma evidência que o cite
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in part.splitlines() if ln.startswith("| ")]
    return rows[1:]  # sem o cabeçalho (a linha |---| não começa por "| ")


def _evidence(cell: str) -> list[re.Match]:
    out = []
    for tok in re.findall(r"`([^`]+)`", cell):
        m = EVIDENCE.match(tok)
        if m and FILE_LIKE.search(m["path"]):
            out.append(m)
    return out


def _live_ids() -> set[str]:
    s = PENDENCIAS.read_text(encoding="utf-8")
    s4 = s[s.index("## 4. Tabela única"):s.index("## 4.1")]
    return {ln.strip("|").split("|")[0].strip() for ln in s4.splitlines() if ln.startswith("| ") and not ln.startswith("| ID ")}


@pytest.fixture(scope="module")
def mapping():
    text = MAPPING.read_text(encoding="utf-8")
    return {
        "text": text,
        "clauses": _table(text, "## Cláusulas 4–10"),
        "annex": _table(text, "## Anexo A"),
    }


def _anm_root() -> Path | None:
    env = os.environ.get("ANM_REPO_ROOT")
    for cand in ([Path(env)] if env else []) + [REPO_ROOT.parent / "agent-network-mcp"]:
        if (cand / "lib").is_dir():
            return cand
    return None


def test_todas_as_clausulas_e_controlos_uma_vez(mapping):
    clauses = [r[0] for r in mapping["clauses"]]
    annex = [r[0] for r in mapping["annex"]]
    assert sorted(clauses) == sorted(CLAUSES), set(clauses) ^ set(CLAUSES)
    assert sorted(annex) == sorted(ANNEX_A), set(annex) ^ set(ANNEX_A)
    assert len(ANNEX_A) == 38 and len(CLAUSES) == 27


def test_estados_validos(mapping):
    for r in mapping["clauses"]:
        assert len(r) == 5, r
        assert r[2] in STATES and r[2] != "N/A", f"{r[0]}: cláusulas 4–10 são obrigatórias"
    for r in mapping["annex"]:
        assert len(r) == 6, r
        assert r[2] in ("Sim", "Não") and r[3] in STATES, r[0]
        assert (r[2] == "Não") == (r[3] == "N/A"), f"{r[0]}: Aplicável=Não se e só se N/A"
        if r[3] == "N/A":
            assert r[4] not in ("", "—"), f"{r[0]}: exclusão sem justificação"


def test_cumpre_e_parcial_tem_evidencia_e_lacunas_tem_item_vivo(mapping):
    live = _live_ids()
    rows = [(r[0], r[2], r[3], r[4]) for r in mapping["clauses"]] + [(r[0], r[3], r[4], r[5]) for r in mapping["annex"]]
    for cid, state, ev, item in rows:
        if state in ("Cumpre", "Parcial"):
            assert _evidence(ev), f"{cid}: {state} sem evidência verificável"
        if state in ("Parcial", "Falta"):
            ids = [x.strip() for x in item.split(",") if x.strip() not in ("", "—")]
            assert ids, f"{cid}: {state} sem item no PENDENCIAS"
            missing = [i for i in ids if i not in live]
            assert not missing, f"{cid}: itens que não estão vivos no PENDENCIAS §4: {missing}"


def test_evidencias_do_nas_existem(mapping):
    rows = [(r[0], r[3]) for r in mapping["clauses"]] + [(r[0], r[4]) for r in mapping["annex"]]
    problems = []
    for cid, ev in rows:
        for m in _evidence(ev):
            if m["anm"]:
                continue
            p = REPO_ROOT / m["path"]
            if not p.is_file():
                problems.append(f"{cid}: {m['path']} não existe")
            elif m["sym"] and m["sym"] not in p.read_text(encoding="utf-8"):
                problems.append(f"{cid}: `{m['sym']}` não aparece em {m['path']}")
    assert not problems, problems


def test_evidencias_do_anm_existem(mapping):
    root = _anm_root()
    if root is None:
        pytest.skip("clone do agent-network-mcp não disponível (ANM_REPO_ROOT)")
    rows = [(r[0], r[3]) for r in mapping["clauses"]] + [(r[0], r[4]) for r in mapping["annex"]]
    problems = []
    for cid, ev in rows:
        for m in _evidence(ev):
            if not m["anm"]:
                continue
            p = root / m["path"]
            if not p.is_file() or (m["sym"] and m["sym"] not in p.read_text(encoding="utf-8")):
                problems.append(f"{cid}: ANM:{m['path']}::{m['sym']}")
    assert not problems, problems


def test_resumo_bate_com_as_tabelas(mapping):
    def row(name):
        m = re.search(rf"^\| {re.escape(name)} \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|$", mapping["text"], re.M)
        assert m, name
        return [int(x) for x in m.groups()]

    for name, rows, col in (("Cláusulas 4–10", mapping["clauses"], 2), ("Anexo A", mapping["annex"], 3)):
        c = Counter(r[col] for r in rows)
        assert row(name) == [c[s] for s in STATES], f"resumo de {name} desactualizado: {dict(c)}"


def test_politica_tem_as_decisoes_da_p40():
    text = POLICY.read_text(encoding="utf-8")
    for needle in ("P-40", "NAS + ANM", "maestro", "DEV", "Claude", "trimestral", "semestral",
                   "GOV-42001-1", "GOV-IMPACT-1", "Não é uma certificação"):
        assert needle in text, needle
