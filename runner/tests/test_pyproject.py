"""PKG-1: o pyproject.toml e o requirements.txt dizem as mesmas dependências (sem divergir em silêncio)."""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _nome(spec: str) -> str:
    return re.split(r"[<>=!~\[ ;]", spec.strip(), maxsplit=1)[0].lower().replace("_", "-")


def _requirements() -> dict[str, str]:
    out = {}
    for ficheiro in ("requirements.txt", "requirements-langgraph.txt"):
        for line in (ROOT / "runner" / ficheiro).read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line and not line.startswith("-r"):
                out[_nome(line)] = line
    return out


def test_pyproject_cobre_todas_as_dependencias_do_requirements():
    proj = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    declaradas = {_nome(d) for d in proj["dependencies"]}
    for extra, deps in proj["optional-dependencies"].items():
        if extra != "all":
            declaradas |= {_nome(d) for d in deps}
    assert declaradas == set(_requirements()), "pyproject.toml e runner/requirements.txt divergem"


def test_pyproject_pins_exactos_iguais_ao_requirements():
    proj = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    todas = list(proj["dependencies"]) + [d for e, ds in proj["optional-dependencies"].items() if e != "all" for d in ds]
    req = _requirements()
    for spec in todas:
        n = _nome(spec)
        assert spec.replace(" ", "") == req[n].replace(" ", ""), f"{n}: {spec!r} != {req[n]!r}"


def test_nucleo_so_tem_pacotes_leves():
    proj = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    nucleo = {_nome(d) for d in proj["dependencies"]}
    assert not nucleo & {"mcp", "psycopg", "langgraph", "groundwright", "fetchtron"}
