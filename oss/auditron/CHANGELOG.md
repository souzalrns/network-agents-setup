# Changelog

Todas as mudanças notáveis deste projecto. Formato: [Keep a Changelog](https://keepachangelog.com/);
versões em [SemVer](https://semver.org/).

## [0.1.0] — 2026-10-09

### Added

- Primeiro corte. Orquestra três engines open-source numa só passagem:
  `pip-audit` (CVEs de dependências Python), `bandit` (SAST Python) e `zizmor` (segurança dos
  workflows do GitHub Actions).
- Modelo comum de achados (`Finding`/`ToolRun`/`ScanResult`) e três níveis SARIF (note/warning/error).
- Relatórios: texto para a consola, JSON e **SARIF 2.1.0** (um `run` por engine, com a versão real).
- Política por `auditron.toml` (`blocking`/`disabled` por engine); por omissão só o `pip-audit`
  bloqueia. Um engine que rebenta, se for bloqueante, bloqueia.
- CLI `auditron scan [PATH] [--config] [--only] [--sarif] [--json] [--quiet]`.
- Workflow de exemplo acoplável (`examples/auditron.yml`) e CI próprio (`.github/workflows/auditron.yml`).
- 25 testes (unitários offline + integração com os engines reais, que saltam se faltarem).
