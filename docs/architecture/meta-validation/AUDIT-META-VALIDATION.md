# AUDIT-META-VALIDATION.md — Validação das recomendações anteriores (padrão ouro)

Este documento responde às 7 perguntas de validação cruzada pedidas: para cada auditoria/decisão anterior, a recomendação foi exagerada? O que cobre de facto, o que falta, verificado por código — não por confiança no resumo anterior.

## 1. Governança — "Adotem o AGT, agentgateway, ContextForge"

**Já respondido com rigor total em `governance/audit/AUDIT-GOVERNANCE.md`** (produzido antes desta sessão) — não refeito aqui, só confirmado por leitura: a recomendação **não** foi "adotem os três". O veredicto real, secção 12 desse documento: AgentMesh → **ADAPTAR** (só módulos de identidade/delegação, sem servidor completo); Cedar → **ADOTAR**; OPA → **OPCIONAL** (redundante se Cedar for escolhido); agentgateway → **NÃO ADOTAR AGORA**; ContextForge → **NÃO ADOTAR AGORA** (exige Redis obrigatório); SPIFFE/SPIRE → **NÃO ADOTAR AGORA**; mcphound → **NÃO ADOTAR** (1 estrela, 6+ meses parado); OpenA2A AIM → **REDUNDANTE**.

CVEs e licenças já verificados nesse documento (secção 7): todas as licenças permissivas (MIT/Apache-2.0), nenhuma CVE nova encontrada especificamente para estes componentes de governança. **Conclusão: a recomendação nunca foi "adotem tudo" — a pergunta parte de uma premissa que a própria auditoria já tinha corrigido.** Nada a acrescentar.

## 2. HITL — "O contrato v1 é suficiente"

**Verificado agora, por leitura direta de `docs/architecture/hitl/README.md` e busca de código — a resposta muda a leitura anterior.**

O `README.md` do contrato tem, no próprio cabeçalho: *"Status: design. Not implemented. Last updated: 2026-09-11"* — mas isto já está **parcialmente desatualizado**: o módulo `runner/plan_runner/hitl.py` (Fase A.2 do plano faseado descrito no próprio README) **já existe e tem testes próprios** (confirmado nesta sessão e na Fase 1 da auditoria de Agentes).

Confirmado por `docs/initiatives/STATUS.md` e por busca de código nesta sessão:

| Fase do plano | Item STATUS.md | Estado real (verificado por código) |
|---|---|---|
| A.1 — Contrato | — | ✅ Feito (`hitl-request-v1.json`) |
| A.2 — Python (`hitl.py`) | **S6a** | ✅ Feito, com testes |
| **A.2b — integração no engine** | **S9** | ❌ **Não feito** — confirmado por busca: zero ocorrências de `import hitl`/`hitl.write_request`/`hitl.read_decision` em `engine.py`, `langgraph_engine.py`, `cli.py` |
| A.3 — TypeScript (`HitlManager.importFromFile/exportToFile`) | **M2** | ❌ Não feito |
| A.4 — Teste end-to-end (Python→Node→Python) | **M3** | ❌ Não feito |

**Resposta direta: o contrato v1 (o desenho) é suficiente para o que se propõe — mas está, na prática, sem efeito nenhum, porque nenhum dos dois motores de execução (`engine.py`/`langgraph_engine.py`) o invoca.** `hitl.py` é uma peça real, testada, e completamente desligada — a mesma classe de achado ("peça construída, nunca ligada") encontrada repetidamente na auditoria de Agentes, agora confirmada também no HITL. M2 e M3 dependem de S9 estar feito primeiro (não há o que sincronizar do lado Node se o lado Python nunca escreve o ficheiro partilhado).

**Classificação:** BUILD — S9 é trabalho de fiação pequeno (ligar 2-3 chamadas já escritas em `hitl.py` aos pontos onde `engine.py` já escreve `human_gate_requested` em `events.jsonl`), não trabalho de desenho novo.

## 3. Agentes — "33 agentes é muito"

**Reverificado nesta sessão por acesso directo ao código-fonte** — correcção ao estado anterior: `MCP-MAPPING.md` descreve o repositório `agent-network-mcp`, que não estava clonado nesta sessão nas passagens anteriores; foi clonado agora (público, `souzalrns/agent-network-mcp`) especificamente para deixar de citar o documento sem poder reabrir a fonte.

Confirmado por leitura directa de `lib/agents.js` (1248 linhas):

- **Contagem exacta: 33 agentes** (`grep` de todas as chaves de topo do objecto, incluindo as com hífen que exigem aspas na chave) — bate certo com o número já citado, não precisou de correcção.
- **3 amostras verificadas ao pé da letra contra o texto real do agente**, não contra o resumo do `MCP-MAPPING.md`: `hvac` (linha 186) menciona de facto "TermoExpert"/"Porto/Gaia" e tem uma **"Matriz de roteamento"** explícita para `refrigeracao-hvac`; `apps-produto` (linha 370) menciona "MesaFlow"/"Alivia"/**"R$34,90"**/"Onze ecrãs de protótipo completos"; `cardiologia` (linha 682) contém literalmente **"repetir entre 1-2h... ou 3-6h"**. As três batem exactamente com o que `MCP-MAPPING.md` tinha citado.

Isto não é "são muitos, cortem" — é uma categorização real por 3 eixos (amplitude/privacidade/origem), com veredicto por agente: 13 horizontal+genérico (migram), 5 vertical+genérico com ingestão real (migram), 10 vertical+proprietário (ficam no MCP privado), 2 casca-por-design (ficam), 3 casca sem razão documentada (pendentes de ingestão), 2 mistos (a dividir). **17 técnicas extraíveis já identificadas → 16 skills novas.** Não há "gordura" por cortar — há trabalho de migração/extração já mapeado e parcialmente executado (G2/G4, confirmado no `STATUS.md`).

**Conclusão:** a pergunta "33 é muito" tem resposta desde antes desta sessão: nenhum agente foi classificado como "sem valor" — todos os 33 têm um destino definido (setup público, MCP privado, ou pendente de decisão). O achado novo desta sessão (Fase 5 da auditoria de Agentes) é complementar, não contraditório: `config/agents.config.ts` (o **catálogo do lado setup**, 24 agentes, diferente dos 33 do `agent-network-mcp`) ainda não tem campo `profile` — a lição de "extrair o genérico do específico" já aplicada manualmente ao `agent-network-mcp` não foi formalizada como mecanismo reutilizável no schema do setup.

## 4. Skills — "50 (67) skills é o suficiente"

**Verificado agora por leitura direta de frontmatter e busca de padrões de enforcement.**

Formato: consistente — `name`, `action`, `version`, `role`, `priority`, `description`, `requires: []` em todas as skills amostradas. Contagem real: **67**, não 50 (confirmado por `find`; o `STATUS.md` já sinalizava esse número como desatualizado desde G2/G4, sem recontagem — corrigido aqui).

**Dependências:** o campo `requires: []` existe no schema, mas não foi verificado nesta sessão se algum mecanismo de carregamento resolve essa lista automaticamente (fora do âmbito desta verificação — ficheiro de código do resolvedor de skills não lido linha a linha).

**Enforcement — achado real:** busca por `enforce|allowed-tools|permission` no corpo das 67 skills devolve só **9 ocorrências** — texto narrativo dentro do corpo (ex. "Enforcement Note" na skill `security-audit`), não um campo estrutural de frontmatter que um sistema de permissões leia e imponha. Isto confirma, por código, o que `patterns-from-hermes/skill-lifecycle.md` já descrevia como *convenção* ("nunca auto-merge") — é disciplina documentada, não imposição técnica.

**Resposta direta:** 67 é o número real, o formato é consistente, mas **enforcement é 100% baseado em disciplina/revisão humana, não em código que impeça uma skill de fazer algo fora do seu `requires`**. Isto não é necessariamente errado para o estágio atual do repo (equipa pequena, sem multi-tenant) — mas é uma lacuna real se/quando skills vierem a ser carregadas dinamicamente por um orquestrador automatizado sem revisão humana no loop.

**Classificação:** REFERENCE (o ciclo de vida já desenhado em `patterns-from-hermes/` é a resposta certa para *quando* promover) / BUILD (se algum dia for preciso enforcement técnico, não só convencional).

## 5. Bootstrap — "CLAUDE.md é suficiente"

**Verificado por leitura direta e comparação de contagens.**

`BOOTSTRAP.md` já resolve o problema original que motivou a sua criação (3 sistemas de estado paralelos sem se conhecerem) e agora lista, após esta sessão, **17 documentos** (os 11 originais de 2026-09-18 + as 6 séries de auditoria produzidas depois, incluindo esta). Isto está a funcionar como pretendido.

**Achados novos, por verificação direta:**
- Existe `AGENTS.md` **na raiz do repo** (regras de skill-orchestration, distinto de `CLAUDE.md`) e um `docs/generated/AGENTS.md` **diferente** (catálogo gerado a partir de `config/agents.config.ts`). Nenhum dos dois está listado em `BOOTSTRAP.md` — o índice cobre `docs/architecture/*`, mas não os dois ficheiros `AGENTS.md` que também são bootstrap.
- `docs/generated/AGENTS.md` está **desatualizado**: declara "Total: 22 agentes", gerado em 2026-08-19; a contagem real de `config/agents.config.ts` hoje é **24** (confirmado por `grep -c "id:"` nesta sessão). O pipeline de regeneração (`pnpm --filter @network-agents/scripts docs:agents`) não foi corrido depois da última alteração ao config.
- A "reconciliação L0 (`CLAUDE.md`/`AGENTS.md`)" identificada como pendente em `FASE1-MEMORIA.md` está, na prática, **menos grave do que sugerido**: os dois ficheiros cobrem escopos diferentes (bootstrap de sessão vs. regras de skill-orchestration), não conteúdo duplicado a divergir — mas continuam sem estar ambos referenciados no mesmo índice, o que é o problema real (descoberta, não conflito de conteúdo).

**Resposta direta:** `CLAUDE.md` sozinho não é suficiente (nunca foi essa a alegação — o próprio `CLAUDE.md` aponta para `BOOTSTRAP.md`), e `BOOTSTRAP.md` está a fazer o trabalho certo, mas tem uma lacuna de cobertura (os `AGENTS.md`) e um achado de doc gerado desatualizado.

**Classificação:** BUILD (pequeno) — acrescentar `AGENTS.md` (raiz) e `docs/generated/AGENTS.md` ao índice de `BOOTSTRAP.md`; rodar `pnpm docs:agents` para corrigir a contagem.

## 6. Segurança — "O B2 resolve tudo"

**Já respondido com honestidade pelo próprio B2**: `SECURITY-AUDIT-FULL.md` secção 5 já se auto-avalia como "4 de 10 riscos cobertos com confiança, 1 inconclusivo, 5 fora do âmbito" — **nunca alegou resolver tudo.** A pergunta "B2 resolve tudo" parte de uma premissa que o próprio documento já refuta explicitamente.

O que esta sessão acrescentou (`security-audit-2026/AUDIT-SECURITY-2026.md`): pesquisa de fontes primárias para tentar fechar os gaps que a sandbox original não conseguiu (rede bloqueada) — resultado: **3 achados concretos e acionáveis novos** (senha hardcoded em `k8s/secrets.yaml`, ausência de RLS em `knowledge_chunks_t6`, ausência total de lockfile Python tornando LLM04 estruturalmente inverificável, não só bloqueado por rede).

**Classificação:** ver `security-audit-2026/AUDIT-SECURITY-2026.md` para a lista completa.

## 7. RAG/Knowledge — "O L5 é a resposta"

**Já respondido, e corrigido nesta sessão** — ver `ingestion-audit/AUDIT-INGESTION.md`: a pergunta "porque está desligado" já não tem a mesma resposta que tinha quando `FASE1-MEMORIA.md` a levantou. **O L5 já foi ligado** (`knowledge_wiring.py`, item S10, confirmado por código real chamado por `engine.py`). O que falta agora não é fiação — é propagação (só 1 de 12 templates usa o bloco `knowledge:`).

**Não confundir S9 (HITL, não feito) com S10 (L5, feito)** — são achados opostos que o `STATUS.md` já registava como itens distintos, e que esta sessão confirmou por leitura de código, não por título de ticket.

---

## Síntese das 7 respostas

| # | Pergunta | Exagero confirmado? | Estado real |
|---|---|---|---|
| 1 | Governança — adotar AGT/etc | **Não** — já era ADAPTAR/ADOTAR seletivo | Sem mudança |
| 2 | HITL — contrato v1 suficiente | **Parcial** — desenho suficiente, execução zero | S9/M2/M3 por fazer |
| 3 | Agentes — 33 é muito | **Não** — já era categorização, não corte | **Reverificado por acesso directo ao repo `agent-network-mcp`** (3 amostras conferidas linha a linha, contagem exacta confirmada); achado complementar: `profile` no setup |
| 4 | Skills — 50/67 suficiente | **Não é exagero, é lacuna de enforcement** | Formato ok, enforcement é disciplina não código |
| 5 | Bootstrap — CLAUDE.md suficiente | **Não era a alegação** | BOOTSTRAP.md funciona, falta indexar 2 ficheiros + regenerar 1 doc |
| 6 | Segurança — B2 resolve tudo | **Nunca foi a alegação** — o próprio B2 diz que não | 3 achados novos e acionáveis |
| 7 | RAG — L5 é a resposta | **Estava certo, e já foi corrigido** | S10 feito, falta propagação (1/12 templates) |

**Achado transversal a todas as 7 respostas:** nenhuma das "recomendações exageradas" presumidas era, de facto, exagerada — as auditorias anteriores já eram, na sua maioria, precisas e auto-críticas. O padrão real encontrado, repetido em quase todas as 7 respostas, é o mesmo da síntese de Agentes (`agents-audit/AUDIT-AGENTS.md` secção 4): **peças reais, verificadas, corretamente desenhadas — e não ligadas, não indexadas, ou não regeneradas.** Não é um problema de decisões erradas. É um problema de o último passo (fiação, indexação, regeneração) ficar sistematicamente por fazer depois da peça estar pronta.
