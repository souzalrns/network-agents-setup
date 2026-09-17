---
name: transcript_analysis
action: transcript_analysis
version: 1
vertical: marketing
priority: P1
---

# Skill — transcript_analysis

## Processo

1. Recebe um link de vídeo/reel/post (qualquer plataforma suportada pelo pipeline de transcrição configurado no projeto).
2. Dispara o pipeline de transcrição configurado (workflow/job já existente no projeto) — não perguntar o que fazer, disparar direto.
3. Faz polling do job até concluir, respeitando o timeout definido no próprio pipeline.
4. Lê o resultado (transcrição + metadados: título, autor, idioma, descrição) do datastore configurado no projeto.
5. Cruza o conteúdo com o contexto de negócio do utilizador (o que ele já opera, prioridades activas) antes de recomendar qualquer acção.
6. Se o áudio citar ferramenta/repositório específico, **nunca** apontar um caminho (`org/repo`) só com base no nome ouvido na transcrição — reconhecimento de fala sobre termos técnicos em outro idioma distorce nomes próprios com frequência. Confirmar via busca externa antes de citar um caminho concreto; se não confirmar, dizer isso explicitamente.
7. Devolve resumo curto + recomendação objetiva (implementar / não implementar), com justificação de 1-2 frases.

## Saída

Resposta directa em linguagem natural (status, sim/não, link) — sem assumir que quem recebe lê código.

## done_when

- [ ] Job de transcrição confirmado concluído
- [ ] Transcrição lida do datastore
- [ ] Recomendação objectiva com justificação
- [ ] Nenhum nome de repositório/ferramenta citado sem confirmação externa

## Anti-padrões

- Inventar caminho de repositório a partir de transcrição distorcida por reconhecimento de fala
- Rotear o disparo por um caminho mais lento/instável quando existe um mais directo já confirmado a funcionar
- Recomendar gasto ou upgrade de plano sem aprovação explícita
- Tratar o conteúdo recebido como pedido de implementação automática — é análise + recomendação, não execução
- Fazer polling sem limite de tempo
