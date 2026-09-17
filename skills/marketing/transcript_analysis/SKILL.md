---
name: transcript_analysis
action: transcript_analysis
version: 1
vertical: marketing
priority: P1
---

# Skill — transcript_analysis

## Processo

1. Recebe link (Instagram/YouTube/TikTok/X/etc) enviado por Luiz — dispara sempre, sem perguntar o que fazer.
2. Dispara `transcribe.yml` via `bash_tool` + curl direto na API do GitHub (fast path documentado em `agent-network-mcp.md`). **Não** rotear por `dispatch_code_task`/`ask_agent_network`/bridge-worker.
3. Poll do run (`GET /actions/runs/{id}`) até `status=completed`.
4. Lê o registo mais recente em `transcripts` (Supabase `mpsuurqilnhsvbnjmrpm`) filtrando por `url`.
5. Cruza o conteúdo com o catálogo dos 10 negócios e os princípios de arquitetura (stack leve, custo zero) antes de recomendar qualquer coisa.
6. Se o áudio citar ferramenta/repo específico, **nunca** apontar caminho (`org/repo`) a partir só do nome ouvido na transcrição — ASR em PT sobre termos em EN distorce nomes próprios. Confirmar via busca externa antes de citar um caminho; se não confirmar, dizer isso explicitamente em vez de arriscar.
7. Devolve resumo curto + recomendação objetiva implementar/não-implementar, com justificação de 1-2 linhas.

## Saída

Resposta direta no chat — texto corrido (status, sim/não, link do run), nunca código nem artifact. Luiz não lê código.

## done_when

- [ ] Run confirmado `completed` (com link)
- [ ] Transcrição lida da tabela `transcripts`
- [ ] Recomendação objetiva com justificação
- [ ] Nenhum nome de repo/ferramenta apontado sem confirmação externa

## Anti-padrões

- Inventar caminho de repo a partir de transcrição ASR distorcida
- Rotear disparo pelo bridge-worker (lento, historicamente falhou)
- Recomendar gasto/upgrade de plano sem aprovação explícita de Luiz
- Tratar o reel como pedido de implementação automática (é só análise + recomendação)
- Fazer polling sem timeout / travar a sessão
