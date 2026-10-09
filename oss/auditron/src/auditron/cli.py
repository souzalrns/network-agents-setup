"""CLI do auditron: `auditron scan [PATH]` corre o gate e sai 0/1 pela política."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auditron import __version__, config, core, report


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="auditron", description="Um gate defensivo de segurança para um repo.")
    p.add_argument("--version", action="version", version=f"auditron {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="correr os engines e sair 0/1 pela política")
    s.add_argument("path", nargs="?", default=".", help="raiz do repo a analisar (por omissão: .)")
    s.add_argument("--config", help="auditron.toml com a política (por omissão: <path>/auditron.toml)")
    s.add_argument("--only", help="correr só estes engines (lista separada por vírgulas)")
    s.add_argument("--sarif", help="gravar o relatório SARIF 2.1.0 neste ficheiro")
    s.add_argument("--json", dest="json_out", help="gravar o relatório JSON neste ficheiro")
    s.add_argument("--quiet", action="store_true", help="não imprimir o relatório de texto")
    return p


def main(argv: list[str] | None = None) -> int:
    opts = _build_parser().parse_args(argv)
    if opts.cmd != "scan":  # pragma: no cover — argparse já exige um subcomando
        return 2

    target = Path(opts.path).resolve()
    if not target.is_dir():
        print(f"error: {opts.path} não é uma pasta", file=sys.stderr)
        return 2

    cfg_path = Path(opts.config) if opts.config else target / "auditron.toml"
    try:
        policy = config.load(cfg_path)
    except (ValueError, OSError) as exc:
        print(f"error: política inválida ({exc})", file=sys.stderr)
        return 2

    only = [e.strip() for e in opts.only.split(",") if e.strip()] if opts.only else None
    result = core.scan(target, policy, only=only)

    if opts.sarif:
        Path(opts.sarif).write_text(report.to_sarif(result), encoding="utf-8")
    if opts.json_out:
        Path(opts.json_out).write_text(report.to_json(result), encoding="utf-8")
    if not opts.quiet:
        print(report.to_text(result))

    return 1 if result.blocked() else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
