"""Pegada do setup (plano setup-estrutura-2, passo de medição): quanto custa USAR este repo em máquina fraca.

Mede, sem rede e sem custo de API:
  - tamanho dos ficheiros versionados (git) e nº de .md;
  - dependências de `runner/requirements.txt` (nº e tamanho instalado, MB; os MB dependem do que está instalado na máquina);
  - uma corrida de plano em modo `stub` com o motor nativo: tempo de parede (mediana de N) e memória residente máxima;
  - RAM de arranque do CLI (`--help`).

Uso (a partir da raiz do repo):
    python scripts/setup_footprint.py            # imprime o relatório
    python scripts/setup_footprint.py --json     # JSON
    python scripts/setup_footprint.py --check    # sai com 1 se passar dos tetos de docs/ops/FOOTPRINT-BASELINE.json
    python scripts/setup_footprint.py --write-baseline   # grava a medição actual como base (tetos = medição + folga)

Os tetos servem para o setup não engordar sem ninguém reparar; não são promessas de desempenho.
"""
from __future__ import annotations

import argparse
import json
import re
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "ops" / "FOOTPRINT-BASELINE.json"
PLAN = ROOT / "docs" / "orchestration" / "marketing" / "templates" / "examples" / "ship-parallel.plan.yaml"
SLACK = {"repo_tracked_mb": 1.25, "runner_deps_mb": 1.25, "stub_run_seconds": 5.0, "stub_run_peak_mb": 1.5, "cli_peak_mb": 1.5}


def _mb(n: float) -> float:
    return round(n / 1024 / 1024, 1)


def repo_size() -> dict[str, float]:
    files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\0")
    files = [f for f in files if f]
    total = sum((ROOT / f).stat().st_size for f in files if (ROOT / f).is_file())
    return {"repo_tracked_mb": _mb(total), "repo_tracked_files": len(files), "repo_md_files": sum(f.endswith(".md") for f in files)}


def deps_size() -> dict[str, float]:
    names = []
    for line in (ROOT / "runner" / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            names.append(re.split(r"[<>=!~\[ ;]", line, maxsplit=1)[0])
    seen: set[str] = set()
    total = 0
    missing = []

    def walk(name: str) -> None:
        key = name.lower().replace("_", "-")
        if key in seen:
            return
        seen.add(key)
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            missing.append(name)
            return
        nonlocal total
        total += sum(f.locate().stat().st_size for f in (dist.files or []) if f.locate().is_file())
        for req in dist.requires or []:
            if "extra ==" in req:
                continue
            walk(re.split(r"[<>=!~\[ ;(]", req, maxsplit=1)[0])

    for n in names:
        walk(n)
    return {"runner_deps_direct": len(names), "runner_deps_total": len(seen) - len(missing), "runner_deps_mb": _mb(total), "runner_deps_missing": len(missing)}


def _child_peak_mb(cmd: list[str]) -> tuple[float, float, int]:
    """(segundos, pico de RAM em MB, returncode) de um processo filho, medido pelo kernel."""
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t0 = time.perf_counter()
    # nosemgrep: dangerous-subprocess-use-audit
    proc = subprocess.run(cmd, cwd=ROOT / "runner", capture_output=True, text=True)
    dt = time.perf_counter() - t0
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss  # KB no Linux; é o máximo acumulado dos filhos
    return dt, round(max(peak, before) / 1024, 1), proc.returncode


def stub_run(repeats: int) -> dict[str, float]:
    if not PLAN.exists():
        return {}
    times, peaks = [], []
    for _ in range(repeats):
        with tempfile.TemporaryDirectory(dir=ROOT / "pilots") as out:
            dt, peak, rc = _child_peak_mb([sys.executable, "-m", "plan_runner", "run", str(PLAN), "--engine", "native",
                                           "--mode", "stub", "--out", out])
        if rc not in (0, 2):  # 2 = pausou num gate humano (válido)
            raise SystemExit(f"a corrida stub falhou (rc={rc})")
        times.append(dt)
        peaks.append(peak)
    return {"stub_run_seconds": round(statistics.median(times), 2), "stub_run_peak_mb": max(peaks)}


def cli_start() -> dict[str, float]:
    dt, peak, _ = _child_peak_mb([sys.executable, "-m", "plan_runner", "--help"])
    return {"cli_start_seconds": round(dt, 2), "cli_peak_mb": peak}


def measure(repeats: int) -> dict[str, float]:
    m: dict[str, float] = {}
    for part in (repo_size(), deps_size(), cli_start(), stub_run(repeats)):
        m.update(part)
    return m


def check(m: dict[str, float]) -> list[str]:
    if not BASELINE.exists():
        return [f"falta {BASELINE.name} (corre --write-baseline)"]
    ceilings = json.loads(BASELINE.read_text(encoding="utf-8"))["ceilings"]
    return [f"{k}: {m[k]} > teto {v}" for k, v in ceilings.items() if k in m and m[k] > v]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args(argv)
    (ROOT / "pilots").mkdir(exist_ok=True)
    m = measure(args.repeats)
    if args.write_baseline:
        ceil = {k: round(m[k] * f, 2) for k, f in SLACK.items() if k in m}
        BASELINE.write_text(json.dumps({"measured": m, "ceilings": ceil, "note": "tetos = medição × folga; recalcular de propósito, não por reflexo"},
                                       indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"gravado {BASELINE.relative_to(ROOT)}")
    if args.json:
        print(json.dumps(m, indent=2, ensure_ascii=False))
    else:
        for k, v in m.items():
            print(f"{k:24} {v}")
    if args.check:
        problems = check(m)
        for p in problems:
            print("ACIMA DO TETO:", p, file=sys.stderr)
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
