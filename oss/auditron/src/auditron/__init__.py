"""auditron — one defensive security gate for a repository.

Orchestra três engines open-source (pip-audit, bandit, zizmor) numa só passagem, normaliza os
achados num modelo comum, escreve um relatório (JSON + SARIF) e decide o código de saída por uma
política declarada. Auto-contido e acoplável: `pip install auditron` + um workflow, em qualquer repo.

A política da área de segurança deste ecossistema é defensiva: o auditron só LÊ e relata; não ataca
nem corre exploits. As ferramentas ofensivas (pentest, red-team de LLM) são companheiras de
laboratório, documentadas no README, fora deste pacote.
"""

from __future__ import annotations

__version__ = "0.1.0"

from auditron.model import Finding, ScanResult, ToolRun

__all__ = ["Finding", "ScanResult", "ToolRun", "__version__"]
