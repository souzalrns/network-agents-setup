# Estacionados (não descartados)

Itens que não puderam ser implantados nesta cadeia: precisam de produção, credenciais, um consumidor real, upstream ou uma decisão. Cada um tem ID estável no `docs/initiatives/PENDENCIAS.md` e um critério de desbloqueio.

| ID | O quê | Bloqueio | Desbloqueia quando |
|---|---|---|---|
| **F3b-AUTH-1** | Autoridade e conflitos do F3b (P-31 = D, P-32 = B, P-33 = B): `match_knowledge_v3` aditiva, anotação no runner, regra no prompt, flag no MCP | SQL em produção (DEV) e PR no MCP | O DEV pede o arranque; depois corre o SQL da v3 e liga a flag |
| F3-MCP-1 | Validade e autoridade nas linhas do MCP (`project` NULL) | Conector do Claude.ai e posse dos dados (P-30 = A) | Decisão sobre o `ingestDocument` do MCP |
| F3c-DESIGN-1 | Pack `docs/knowledge/design/` no RAG | Nenhum consumidor de `kb: design` (P-36 = A). Desde 2026-10-07 os passos de design já recebem o pack por `repo_files` (opção A) | Um plano ou o conector usar `kb: design` (o teste de cobertura avisa) |
| F3b-GS-1 | Golden set de marketing (~20 casos) | Quota de embeddings e prioridade (P-34 = A) | Quota disponível; o run é do DEV (`l5_eval run`) |
| F3b-VAL-1 | Datas reais em `legal/direito-br-pt.md` e `imobiliario/fipezap.md` | Só o autor sabe as datas (P-28 = C) | O DEV escreve os 2 sidecars |
| **F2-SEC-1** | SSRF por DNS rebinding entre a verificação e o pedido no `fetch` | Limitação conhecida do F2a (`WEB-FETCH.md:40`) | Ligar o pedido ao IP verificado (pinning), num PR do F2 |
| F0.12 | Apagar a `knowledge_chunks_t6` | Irreversível: backup e decisão do DEV | Decisão do DEV (já provado: está toda na canónica) |
| F0.6 / S-003 | Teste real no conector do Claude.ai | O conector não mostra tools (protecção da Vercel) | Uma forma de expor o MCP ao conector |
| F1b | Docling | Sem documentos reais com perda de estrutura medida (P-21) | O DEV entrega PDFs reais |
| P-22 | Contribuição upstream no MarkItDown | Acção pública na conta do DEV | O DEV abre a issue |
| R-006 | O `l5_eval` passa a medir a proveniência da v2 | — | **Feito em PR** (2026-10-07): `provenance_v2_ok` |
| W-011 | O runner valida o `MCP_URL` e o bypass à partida | — | **Feito em PR** (2026-10-07) |
| F6 (canónico) | UM domínio de prova, com o Domain Onboarding Cost medido | D-EP8 (P-23 = A: é outro item, não este F6) | A decisão do domínio |
| F2 (resto canónico) | `discover`, fallback JavaScript | P-24 e P-25 | Confirmação das propostas |
| F3-ART-1 | Proveniência na camada ARTIFACT (`uri`, estado e validade no bloco de conhecimento; fontes no `result.json`) | Prioridade (revisão de 2026-10-07) | PR do Claude, sem produção |
| F4-MAT-1 | Escala de maturidade do E §15.7 (DECLARED … PROVEN) | Decisão P-38 | A decisão; depois, um PR do Claude |
| F5-ROUTE-1 | Run real a partir do `route` (discover → select) | Credenciais do DEV | Um run do DEV |
| AU-20 | O worker executa tools (`read_repo_file`, `retrieve_knowledge`) | Decisão P-37 (recomendada: executor mínimo em Python) | A decisão; depois, PRs do Claude |
