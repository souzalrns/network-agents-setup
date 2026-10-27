# Prontidão da plataforma — gerado

> **Não editar à mão.** Regenerar com: `cd runner && python -m plan_runner.prontidao`
> Fonte: `config/platform-readiness.yaml`. O CI falha se uma prova citada deixar de existir.
> **PROVADA** = testes + run real citado; **TESTADA** = só testes; **SEM PROVA** = nenhum teste.
> As lacunas são itens vivos do `PENDENCIAS.md` (o estado deles vive lá, não aqui).

| Capacidade | Critério de aceitação | Estado | Testes | Runs reais | Lacunas (PENDENCIAS) |
|---|---|---|---:|---:|---|
| Execução de planos | Plano real concluído e artefactos validados | **PROVADA**, com lacunas | 4 | 2 | AU-22b (ABERTO, Baixa) |
| Aprovação humana | Acção protegida bloqueada até existir aprovação válida | **PROVADA**, com lacunas | 5 | 2 | COM-1 (EM CURSO, Média), A13 (ABERTO, Média), OFFICE-A4 (BLOQUEADO, Média) |
| Recuperação | Retoma sem repetir indevidamente acções externas | **PROVADA** | 5 | 1 | — |
| Conhecimento | Resposta com fontes identificáveis e contexto correcto | **PROVADA**, com lacunas | 4 | 2 | F3b-VAL-1 (ABERTO, Média), F6 (EM CURSO, Média) |
| Ferramentas | Selecção e execução dentro das permissões autorizadas | **PROVADA**, com lacunas | 5 | 2 | F2-DISC-1 (ABERTO, Baixa), TRADER-RISK-1 (ABERTO, Baixa) |
| Custos e limites | Limites aplicados e consumo registado | **PROVADA**, com lacunas | 4 | 1 | T-004 (ABERTO, Média) |
| Observabilidade | Reconstrução da execução através dos eventos | **PROVADA**, com lacunas | 4 | 1 | OFFICE-A2 (ABERTO, Média), RUNNER-WHY-1 (ABERTO, Baixa) |
| MCP | Integração real com autenticação e comportamento seguro em caso de falha | **PROVADA**, com lacunas | 3 | 1 | F0.6 (EM CURSO, Média), AU-25 (ABERTO, Baixa), S-003 (BLOQUEADO, Baixa), W-010 (ABERTO, Baixa) |

## Provas por capacidade

### Execução de planos — PROVADA

- teste: `runner/tests/test_real_plans.py::test_seo_article_demo_writes_artifacts`
- teste: `runner/tests/test_done_when.py::test_exists_cumprido_termina_em_done`
- teste: `runner/tests/test_done_when.py::test_exists_em_falta_falha_o_run_com_o_motivo`
- teste: `runner/tests/test_canonical_composition.py::test_run_canonico_hitl_depois_orcamento_depois_done`
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` ("| F5-ROUTE-1 | F5-ROUTE-1 | **PASS** | área marketing (keywords), outcome plan, agente None; estado done")
- run real: `docs/ops/F5-E2E-RUN.md` ("**Veredicto: PASSOU**")

### Aprovação humana — PROVADA

- teste: `runner/tests/test_tool_executor.py::test_tool_act_exige_aprovacao_e_nao_corre`
- teste: `runner/tests/test_external_worker.py::test_worker_nunca_executa_um_passo_com_human_gate`
- teste: `runner/tests/test_external_worker.py::test_reject_no_gate_termina_sem_mais_chamadas`
- teste: `runner/tests/test_done_when.py::test_gate_nao_resolvido_falha_o_run`
- teste: `runner/tests/test_real_plans.py::test_approval_rounds_full_cycle_three_hitls`
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` ("| COM-1 | COM-1 | **PASS** | estado paused_human_gate")
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` ("| F6-MARKET | F6 | **PASS** | estado paused_human_gate")

### Recuperação — PROVADA

- teste: `runner/tests/test_crash_recovery.py::test_crash_recovery_running_state_resumes`
- teste: `runner/tests/test_crash_recovery.py::test_crash_recovery_preserves_completed`
- teste: `runner/tests/test_engine_external.py::test_native_resume_external_completes`
- teste: `runner/tests/test_external_worker.py::test_erro_do_gemini_deixa_waiting_external_sem_result_e_resume_recupera`
- teste: `runner/tests/test_budget.py::test_resume_com_tecto_maior_continua_de_onde_parou`
- run real: `pilots/evidence/setup-close-2026-10-27T015747Z.md` ("| RUNNER-RESUME-1 | RUNNER-RESUME-1 | **PASS** | interrompido depois de research; retomado até paused_human_gate")

### Conhecimento — PROVADA

- teste: `runner/tests/test_rag_canonical.py::test_agente_composto_nunca_devolve_o_mesmo_fragmento_duas_vezes`
- teste: `runner/tests/test_l5_eval.py::test_metricas_contam_rank_de_chunk_fonte_mrr_e_proveniencia`
- teste: `runner/tests/test_f3b_authority.py::test_config_e_sql_tem_os_mesmos_niveis_e_o_mesmo_default`
- teste: `runner/tests/test_security_pipeline.py::test_audit_recebe_o_l5_de_security_com_a_fonte_citada`
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` ("| F3b-GS-1 | F3b-GS-1 | **PASS** | chunk_hit@1 0.6; chunk_hit@4 0.9; source_hit@4 1.0")
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` ("| MCP-V3 | F3b-AUTH-1 | **PASS** | versão do retrieve: v3; authority do 1.º hit: curado")

### Ferramentas — PROVADA

- teste: `runner/tests/test_tool_executor.py::test_tool_nao_autorizada_nao_corre`
- teste: `runner/tests/test_tool_executor.py::test_read_repo_file_le_e_recusa_segredos`
- teste: `runner/tests/test_tool_executor.py::test_args_invalidos_sao_recusados_antes_de_executar`
- teste: `runner/tests/test_web_allowlist.py::test_v1_deny_by_default_e_exclusoes_de_proposito`
- teste: `runner/tests/test_f2_fetch_tool.py::test_plano_de_demonstracao_e_valido_e_usa_a_tool_com_area`
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` ("| F2 | F2 | **PASS** | estado paused_human_gate; passos concluídos: research")
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` (""tool": "fetch_url"")

### Custos e limites — PROVADA

- teste: `runner/tests/test_budget.py::test_worker_para_ao_atingir_o_tecto_sem_chamar_o_gemini`
- teste: `runner/tests/test_engine_external.py::test_native_run_aborts_when_budget_exceeded`
- teste: `runner/tests/test_counttokens.py::test_projected_cost_unknown_price_fails_closed`
- teste: `runner/tests/test_external_worker.py::test_le_request_chama_gemini_escreve_result_e_regista_tokens`
- run real: `docs/ops/WORKER-EXTERNAL.md` ("Primeiro run real (B1): FEITO a 2026-10-01")

### Observabilidade — PROVADA

- teste: `runner/tests/test_f5_evidence.py::test_run_completo_passou`
- teste: `runner/tests/test_f5_evidence.py::test_resumo_nunca_mostra_conteudo_nem_segredos`
- teste: `runner/tests/test_office.py::test_cada_evento_da_o_seu_estado`
- teste: `runner/tests/test_skill_usage.py::test_native_regista_a_skill_de_cada_passo`
- run real: `docs/ops/F5-E2E-RUN.md` ("**Veredicto: PASSOU**")

### MCP — PROVADA

- teste: `runner/tests/test_mcp_knowledge.py::test_retrieve_raises_on_tool_error`
- teste: `runner/tests/test_mcp_knowledge.py::test_retrieve_raises_on_empty_response`
- teste: `runner/tests/test_mcp_knowledge.py::test_retrieve_passes_kb_query_topk_and_require_citations`
- run real: `pilots/evidence/setup-close-2026-10-27T002056Z.md` ("| MCP-V3 | F3b-AUTH-1 | **PASS**")
