"""Integração: os engines reais contra fixtures sintéticas. Saltam se a ferramenta faltar."""

from __future__ import annotations

from auditron import scanners
from auditron.config import DEFAULT
from auditron.core import scan
from tests.conftest import requires


@requires("bandit")
def test_bandit_apanha_shell_true(bad_repo):
    run = scanners.bandit(bad_repo, blocking=False)
    assert run.error is None and run.version.startswith("bandit")
    assert any(f.rule_id == "B602" and f.level == "error" for f in run.findings)
    assert all(f.location == "pkg/bad.py" for f in run.findings)  # caminho relativo ao alvo


@requires("bandit")
def test_bandit_limpo_no_repo_inocuo(clean_repo):
    assert scanners.bandit(clean_repo, blocking=False).ok


@requires("zizmor")
def test_zizmor_apanha_template_injection(bad_repo):
    run = scanners.zizmor(bad_repo, blocking=False)
    assert run.error is None
    assert any(f.rule_id.endswith("template-injection") and f.level == "error" for f in run.findings)


@requires("zizmor")
def test_zizmor_sem_workflows_e_limpo(clean_repo):
    assert scanners.zizmor(clean_repo, blocking=False).ok


@requires("pip-audit")
def test_pip_audit_apanha_vuln_conhecida_sem_duplicar(bad_repo):
    result = scan(bad_repo, DEFAULT)  # passa pelo dedupe do core
    pa = next(r for r in result.runs if r.tool == "pip-audit")
    assert pa.error is None and pa.blocking and pa.findings
    ids = [f.rule_id for f in pa.findings]
    assert len(ids) == len(set((f.rule_id, f.message) for f in pa.findings))  # sem duplicados
    assert result.blocked() is True  # pip-audit bloqueia


@requires("pip-audit")
def test_pip_audit_sem_requirements_e_limpo(clean_repo):
    assert scanners.pip_audit(clean_repo, blocking=True).ok


def test_engine_em_falta_vira_erro_e_bloqueia_se_bloqueante(monkeypatch, clean_repo):
    monkeypatch.setattr(scanners.shutil, "which", lambda _t: None)  # finge que nada está instalado
    run = scanners.pip_audit(clean_repo, blocking=True)
    assert run.error and "não está instalado" in run.error
