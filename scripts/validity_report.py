"""F3b, P-29 = A: relatório local da validade das fontes do L5 (só leitura, sem BD nem rede).

Lê o MANIFEST (`scripts/ingest_delta.py`), os sidecars `<nome>.meta.yaml` e a política
(`config/knowledge-validity.yaml`). O git é a fonte de verdade do T6: o que está aqui é o que
o `ingest_apply` grava na `knowledge_sources`. Não é um workflow (P-29: sem minutos pagos);
corre-se à mão:

    python scripts/validity_report.py                 # Markdown
    python scripts/validity_report.py --json
    python scripts/validity_report.py --at 2027-01-01  # como estará nessa data
    python scripts/validity_report.py --strict        # exit 1 se houver expirados ou datas em falta

Os expirados não são apagados (P-29 = A): ficam na BD e a `match_knowledge_v2` deixa-os de
fora por omissão. O relatório diz quais renovar, revogar ou datar.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))

from plan_runner.provenance import ProvenanceError, load_meta  # noqa: E402
from plan_runner.validity import load_policy, validity_state  # noqa: E402
from scripts.ingest_delta import MANIFEST, sha256_file  # noqa: E402

ATTENTION = ("expirado", "a_expirar", "falta_data", "sidecar_invalido", "ainda_nao_vigora")
STRICT_FAIL = ("expirado", "falta_data", "sidecar_invalido")


def collect(root: Path, at: datetime, policy_path: Path | None = None) -> dict:
    policy = load_policy(policy_path or root / "config" / "knowledge-validity.yaml")
    rows = []
    for rel, _agent, _prio in MANIFEST:
        full = root / rel
        if not full.is_file():
            rows.append({"source": rel, "class": None, "state": "em_falta", "detail": "não existe"})
            continue
        try:
            meta = load_meta(full, sha256_file(full)[0])
        except ProvenanceError as exc:
            rows.append({"source": rel, "class": None, "state": "sidecar_invalido", "detail": str(exc)})
            continue
        rows.append(validity_state(policy, rel, meta, at=at))
    return {
        "at": at.isoformat(timespec="seconds"),
        "expiring_within_days": policy.expiring_within_days,
        "counts": dict(sorted(Counter(r["state"] for r in rows).items())),
        "rows": rows,
    }


def to_markdown(report: dict) -> str:
    attention = [r for r in report["rows"] if r["state"] in ATTENTION]
    title = (
        f"**Validade das fontes do L5 em {report['at']}** "
        f"(a expirar = nos próximos {report['expiring_within_days']} dias)"
    )
    lines = [
        title,
        "",
        "Contagens: " + ", ".join(f"{k} {v}" for k, v in report["counts"].items()),
        "",
    ]
    if not attention:
        lines.append("Nada a fazer: nenhuma fonte expirada, a expirar ou sem a data que a classe exige.")
        return "\n".join(lines)
    lines += ["| Fonte | Classe | Estado | Desde | Até | Detalhe |", "|---|---|---|---|---|---|"]
    for r in attention:
        detail = (r.get("detail") or "").replace("|", "/")
        lines.append(
            f"| `{r['source']}` | {r.get('class') or '—'} | **{r['state']}** | "
            f"{r.get('effective_from') or '—'} | {r.get('effective_until') or '—'} | {detail} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Relatório de validade das fontes do L5 (F3b).")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--at", help="Instante ISO 8601 (por omissão: agora, UTC)")
    parser.add_argument("--strict", action="store_true", help="exit 1 se houver expirados ou datas em falta")
    opts = parser.parse_args(argv)
    at = datetime.fromisoformat(opts.at) if opts.at else datetime.now(UTC)
    report = collect(ROOT, at if at.tzinfo else at.replace(tzinfo=UTC))
    print(json.dumps(report, ensure_ascii=False, indent=2) if opts.json else to_markdown(report))
    if opts.strict and any(r["state"] in STRICT_FAIL for r in report["rows"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
