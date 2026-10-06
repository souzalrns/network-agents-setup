# Decisões P-21 a P-36

Texto completo, com as opções A/B/C, em `docs/initiatives/PENDENCIAS.md` §10. Aqui fica só a escolha.

| ID | Tema | Escolha | Data | Estado |
|---|---|---|---|---|
| P-21 | F1b: Docling | A: não necessário por agora (sem documentos reais com perda medida) | 2026-10-05 | Proposta |
| P-22 | Contribuição upstream no `microsoft/markitdown` | B: primeiro uma issue, aberta pelo DEV na conta dele | 2026-10-05 | Proposta |
| P-23 | F6 da cadeia vs F6 canónico | A: os 2. O da cadeia fecha neste pacote; o canónico (domínio de prova, D-EP8) continua | 2026-10-06 | Aplicada por instrução do maestro ("Fez o f6 como no prompt"); falta a confirmação formal no §10 |
| P-24 | F2: `scrape.yml` do MCP | A: manter como legado; o que vai para o L5 passa pelo `fetch` | 2026-10-06 | Proposta |
| P-25 | F2: allowlist por área | B: `--allow` explícito em cada chamada, até ao 1.º uso real | 2026-10-06 | Proposta |
| P-26 | F3: proveniência no retrieve | A: aditiva (`match_knowledge_v2`), MCP atrás de flag | 2026-10-06 | **Decidida** (maestro) |
| P-27 | F3b: que fontes têm data | C: só legal, mercado e web | 2026-10-06 | **Decidida** |
| P-28 | F3b: quem define a data | C: o autor no sidecar; TTL de 90 dias só para a web | 2026-10-06 | **Decidida** |
| P-29 | F3b: expirados | A: ficam na BD e são filtrados; relatório local | 2026-10-06 | **Decidida** |
| P-30 | F3b: linhas do MCP | A: o F3b cobre só o T6 → F3-MCP-1 | 2026-10-06 | **Decidida** |
| P-31 | F3b: conflitos | D: supersessão explícita + as 2 fontes com anotação | 2026-10-06 | **Decidida** (implementação estacionada: F3b-AUTH-1) |
| P-32 | F3b: autoridade | B: 3 níveis por path, override no sidecar, `match_knowledge_v3` aditiva | 2026-10-06 | **Decidida** (implementação estacionada: F3b-AUTH-1) |
| P-33 | F3b: filtrar por autoridade | B: devolve tudo; `min_authority` opcional | 2026-10-06 | **Decidida** (implementação estacionada: F3b-AUTH-1) |
| P-34 | F3b: golden set | A: marketing + sintéticos no CI + R-006 | 2026-10-06 | **Decidida** (sintéticos de validade no #120; marketing → F3b-GS-1) |
| P-35 | F3c: destino dos 32 `.md` | A: migrar 7 de marketing; `EXCLUDED` com razão para 25 | 2026-10-06 | **Decidida** (#119) |
| P-36 | F3c: pack de design | A: excluir até haver consumidor → F3c-DESIGN-1 | 2026-10-06 | **Decidida** (#119) |
