"""Relatórios: texto para a consola, JSON para máquinas, SARIF 2.1.0 para o GitHub code scanning.

O SARIF leva um `run` por engine (com a versão real), para os achados aparecerem agrupados e
rastreáveis na aba Security do GitHub.
"""

from __future__ import annotations

import json

from auditron import __version__
from auditron.model import ScanResult, level_rank

SARIF_SCHEMA = "https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json"


def to_json(result: ScanResult) -> str:
    return json.dumps(result.as_dict(), ensure_ascii=False, indent=2)


def to_sarif(result: ScanResult) -> str:
    runs = []
    for tr in result.runs:
        rules: dict[str, dict] = {}
        results = []
        for f in tr.findings:
            rules.setdefault(f.rule_id, {"id": f.rule_id})
            phys = {"artifactLocation": {"uri": f.location or "."}}
            if f.line:
                phys["region"] = {"startLine": f.line}
            results.append(
                {
                    "ruleId": f.rule_id,
                    "level": f.level,
                    "message": {"text": f.message},
                    "locations": [{"physicalLocation": phys}],
                }
            )
        runs.append(
            {
                "tool": {
                    "driver": {
                        "name": tr.tool,
                        "version": tr.version or "unknown",
                        "informationUri": "https://github.com/souzalrns/network-agents-setup/tree/main/oss/auditron",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        )
    return json.dumps({"version": "2.1.0", "$schema": SARIF_SCHEMA, "runs": runs}, ensure_ascii=False, indent=2)


_ICON = {"error": "✗", "warning": "!", "note": "·"}


def to_text(result: ScanResult) -> str:
    lines = [f"auditron {__version__} — {result.target}"]
    for tr in result.runs:
        tag = "BLOQUEIA" if tr.blocking else "informa"
        if tr.error:
            lines.append(f"  {tr.tool} ({tag}): ERRO — {tr.error}")
            continue
        c = tr.counts()
        head = "limpo" if tr.ok else f"error {c['error']}, warning {c['warning']}, note {c['note']}"
        lines.append(f"  {tr.tool} {tr.version} ({tag}): {head}")
        for f in sorted(tr.findings, key=lambda x: -level_rank(x.level))[:50]:
            where = f.location + (f":{f.line}" if f.line else "")
            lines.append(f"      {_ICON.get(f.level, '·')} [{f.rule_id}] {where} — {f.message[:140]}")
    verdict = "BLOQUEADO" if result.blocked() else "ok"
    lines.append(f"veredicto: {verdict}")
    return "\n".join(lines)
