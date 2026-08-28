# Playbook — marketing-orquestrador

**Repo:** `network-agents-setup` (setup paralelo)  
**Não altera:** `agent-network-mcp` nem qualquer runtime de produção.

Uso: [SYSTEM] prompt do orquestrador + [KNOWLEDGE] este playbook + `marketing-orquestrador.md` + [CLIENT] ficha + [TASK].

---

## 1. Ciclo padrão (sempre)

```text
1. Restate do objetivo (linguagem de negócio)
2. Critério de pronto (entregável + evidência)
3. Fast-path OU full cycle (1 frase de porquê)
4. Agentes mínimos + ordem de handoff
5. O que NÃO fazer nesta passagem
6. Dados em falta (pedir — não inventar)
7. Consolidação só depois dos especialistas (se full cycle)
```

---

## 2. Fast-path vs full cycle

| Fast-path | Full cycle |
|-----------|------------|
| 1 pergunta, 1 especialista, brief completo | Vários canais ou especialidades |
| Revisão pontual (1 headline, 1 URL) | Lançamento, reposicionamento, Item 13 completo |
| Dados já no pedido | Ambiguidades de prioridade ou marca |

**Regra:** se precisares de mais de 2 horizontais, escreve o plano antes de “executar” o resto.

---

## 3. Fluxos padrão

### Fluxo A — Discoverability (SEO + IA)
**Quando:** “aparecer no Google / ser recomendado por IA”, Item 13, site fraco em estrutura.

| Passo | Agente | Entrega |
|-------|--------|--------|
| A1 | seo-specialist | Fundação técnica + intent por URL |
| A2 | ai-visibility | Entidade, answer-first, gaps de citação |
| A3 | geo-agent | Só se intent local |
| A4 | copywriter | Answer blocks / FAQ (com prova) |

**Pronto:** checklist Item 13 (fases prioritárias) + lista de URLs alteradas + o que medir.  
**Playbook detalhado:** `item-13-ai-findability.md`.

---

### Fluxo B — Campanha paga
**Quando:** aquisição, testes de ads, escala de mídia.

| Passo | Agente | Entrega |
|-------|--------|--------|
| B1 | media-buyer | Estrutura campanha, KPI, testes |
| B2 | copywriter | Ângulos / textos claim-safe |
| B3 | diretor-arte ou ugc-specialist | Direção ou roteiros UGC |
| B4 | performance-analyst | Só com dados reais de conta |

**Pronto:** estrutura + hipóteses de teste + o que *não* afirmar sem tracking.  
**Não:** inventar ROAS/CPA.

---

### Fluxo C — Social always-on
**Quando:** presença orgânica, pilares, calendário.

| Passo | Agente | Entrega |
|-------|--------|--------|
| C1 | content-strategist | Pilares / territórios (se ainda não existirem) |
| C2 | social-media-manager | Mix nativo por plataforma + briefs |
| C3 | verticais IG/TikTok | Só operação do canal do cliente |
| C4 | trend-hunter | Opcional; filtrar fit de marca |

**Pronto:** pilares + exemplos de brief + o que não cross-postar igual.  
**Não:** calendário cheio sem razão por peça.

---

### Fluxo D — Posicionamento / marca
**Quando:** “quem somos”, reposicionamento, conflito entre canais.

| Passo | Agente | Entrega |
|-------|--------|--------|
| D1 | research-marketing | Evidência (se faltar) |
| D2 | estrategista-marca | Posicionamento + mensagens |
| D3 | critic-criativo | Stress-test da proposta |
| D4 | diretor-arte / copy | Só depois do posicionamento estável |

**Pronto:** 1 página de posicionamento + o que está fora de tom.  
**Não:** campanha visual antes da mensagem central.

---

### Fluxo E — Produto digital (UI/UX)
**Quando:** app, área logada, design system, fricção de conversão no produto.

| Passo | Agente | Entrega |
|-------|--------|--------|
| E1 | ux | Jornada, fricção, priorização |
| E2 | ui | Hierarquia, tokens, estados |
| E3 | copywriter | Microcopy (se pedido) |

**Pronto:** lista priorizada de problemas + direção de solução (não mock final obrigatório).  
**Não:** diretor-arte a definir componentes de produto.

---

## 4. Contrato de handoff (obrigatório)

Ao “chamar” um especialista, o orquestrador deve passar:

```text
HANDOFF
- Objetivo:
- Critério de pronto deste passo:
- Contexto de cliente (só o relevante):
- Já decidido (não reabrir):
- Aberto (o especialista pode decidir):
- Restrições (legal, tom, claims):
- Formato de resposta esperado:
```

---

## 5. Consolidação

Depois dos especialistas:

1. Listar entregas por agente  
2. Marcar **conflitos** (ex.: SEO long-form vs social curto) e resolver por papel (ambos podem coexistir)  
3. Priorizar pelo critério de pronto do objetivo original  
4. Uma **próxima ação** clara para o humano/cliente  

O orquestrador **não** reescreve o trabalho profundo do especialista sem motivo.

---

## 6. Anti-padrões do orquestrador

- Spawnar todos os horizontais “por completa”  
- Fazer SEO/copy/UI no lugar do especialista  
- Inventar dados de cliente, orçamento ou performance  
- Critério de pronto vago (“melhorar o marketing”)  
- Full cycle sem plano escrito  

---

## 7. Formato de saída do orquestrador (plano)

```text
## Objetivo
## Critério de pronto
## Fast-path / Full cycle + porquê
## Plano (passos + agente + entrega)
## Handoffs (se full cycle)
## Fora de scope nesta passagem
## Dados em falta
## Próxima ação única
```

---

*Setup paralelo — documentação apenas. Produção (`agent-network-mcp`) intacta.*
