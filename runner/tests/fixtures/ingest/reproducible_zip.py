"""Torna reprodutível um ficheiro OOXML (DOCX/XLSX), que é um ZIP.

O python-docx e o openpyxl gravam cada entrada do ZIP com a hora actual. Este helper
re-empacota as mesmas entradas, pela mesma ordem e com o mesmo conteúdo, com uma data fixa e
permissões fixas. O resultado é byte a byte igual em cada corrida (com as mesmas versões dos
geradores, fixadas em `runner/requirements-fixtures.txt`).
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Callable

FIXED_ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def normalize_zip(data: bytes, patches: dict[str, Callable[[bytes], bytes]] | None = None) -> bytes:
    """Re-empacota com data fixa; `patches` corrige o conteúdo de entradas pelo nome."""
    patches = patches or {}
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as dst:
        for info in src.infolist():
            fixed = zipfile.ZipInfo(info.filename, date_time=FIXED_ZIP_DATE)
            fixed.compress_type = zipfile.ZIP_DEFLATED
            fixed.external_attr = 0o644 << 16
            content = src.read(info.filename)
            if info.filename in patches:
                content = patches[info.filename](content)
            dst.writestr(fixed, content, compresslevel=9)
    return out.getvalue()
