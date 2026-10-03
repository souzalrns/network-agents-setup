Sim. **Fui ao Git antes de responder**, porque aqui vale a pena validar o documento contra o estado real e não apenas contra o que discutimos.

Minha conclusão: **o documento está muito forte, mas eu não o mandaria ainda ao Claude Code.** Ele capturou quase todo o raciocínio estratégico, porém encontrei alguns pontos que, se não forem incorporados, podem fazer exatamente o que você quer evitar: **algo importante ficar perdido ou uma informação antiga ser tomada como verdade atual**.

O mais importante é que encontrei **uma contradição real no próprio Git sobre o estado do L5**.

---

# 1. Primeiro: #61 está realmente merged

Verifiquei `main`.

O HEAD atual é:

`969d3cef...`

com:

> Merge pull request #61 — SEC-2d triagem do semgrep + SEC-2b fechado

E o commit #61 registra:

* SEC-2d concluído;
* 0 achados no código ativo;
* 49 achados restantes somente em código arquivado;
* SEC-2b fechado;
* chave antiga neutralizada;
* `OPEN-ITEMS`, `STATUS` e `.gitleaksignore` atualizados.

Portanto, **a pista SEC-1/SEC-2 que vocês estavam fechando pode ser considerada encerrada**.

Mas há uma nuance importante:

> **Security engineering track ≠ Security capability 100% pronta.**

O `security-capabilities.yaml` atual ainda declara:

* `triage` → implemented
* `defensive_audit` → implemented
* `security_report` → implemented
* `secrets_hygiene` → partial
* `supply_chain` → partial
* `mcp_surface` → partial
* `hardening_recommend` → partial
* `agent_redteam_lab` → deferred

Portanto eu escreveria:

**“Pista SEC-1/SEC-2 fechada”**

e não:

**“Security 100% fechada.”**

Isso evita confundir segurança da infraestrutura com maturidade do Domain Pack.

---

# 2. A maior correção: L5 não pode aparecer simplesmente como “não verificado”

Aqui encontrei uma inconsistência documental importante.

O seu plano diz:

> Knowledge L5 — pgvector + ingest (prova incompleta)

e F0 diz:

> confirmar que `security-agents-stack.md` está ingerido no Supabase.

Porém o Git contém documentação afirmando que **C8 foi fechado**, com:

* 110 chunks;
* markdown → chunk → embedding → Supabase;
* retrieve via `McpKnowledge`;
* pipeline completo.

E a `ECOSYSTEM.md` diz explicitamente:

> RAG já construído e a funcionar.

Ao mesmo tempo, `T6-INGEST-PIPELINE.md` descreve o pipeline de ingestão incremental e a `STATUS` registra que a tabela canónica mudou para `knowledge_chunks`.

### Portanto o problema não é simplesmente “L5 não existe”.

O problema correto é:

> **O L5 possui evidência histórica de funcionamento, mas o estado atual da cobertura, da ingestão do Security Pack e da qualidade do retrieval precisa ser revalidado contra a infraestrutura canónica atual.**

Isso muda bastante o F0.

Eu colocaria:

```text
F0 — REVALIDAÇÃO L5

1. Confirmar tabela canónica atual: knowledge_chunks
2. Confirmar sources/chunks existentes
3. Confirmar que security pack está efetivamente ingerido
4. Executar retrieval real
5. Medir golden set
6. Confirmar provenance atualmente disponível
7. Comparar estado atual com evidência C8
```

Ou seja:

**não reconstruir C8. Revalidar C8 no estado atual.**

Isso está muito mais alinhado com a regra:

> NÃO CONSTRUIR O QUE JÁ EXISTE.

---

# 3. Existe outra coisa importante que o plano está subestimando: o `packages/core`

O seu documento diz:

> Universal Core — já operacional

Isso é verdadeiro **se estivermos falando do `plan_runner` + serviços efetivamente utilizados**.

Mas pode induzir o Claude Code a interpretar que `packages/core` também está operacional.

A auditoria `CORE-MAPPING.md` mostra:

* 5 REAL
* 19 INCOMPLETO
* 14 MOCK
* 1 barrel

E existem mocks relevantes, inclusive:

* `SecurityManager`
* `WorkerSupervisor`
* `IngestionOrchestrator`
* `CompletenessValidator`
* `Orchestrator` — embora exista uma auditoria posterior que corrige a classificação desse módulo, portanto **não devemos reutilizar cegamente o CORE-MAPPING antigo**.

Isso é especialmente importante porque o `BOOTSTRAP.md` registra uma regra fundamental:

> há vários documentos históricos e alguns já foram corrigidos por auditorias posteriores.

### Eu adicionaria ao plano uma seção:

**“Estado de verdade documental”**

com:

```text
ACTIVE SOURCE
docs/initiatives/OPEN-ITEMS.md
docs/initiatives/STATUS.md
docs/architecture/BOOTSTRAP.md
EXECUTION-PLAN.md

HISTORICAL / EVIDENCE
docs/STATUS.md
docs/STATUS-ECOSSISTEMA.md
etc.

AUDIT OVERRIDES
quando uma auditoria posterior contradiz um mapa anterior,
a auditoria posterior prevalece.
```

Isso é extremamente importante para o seu objetivo de não deixar conhecimento perdido.

---

# 4. Está faltando uma regra que considero essencial: “não confiar no inventário sem revalidação”

Vocês já descobriram isso várias vezes.

O próprio Git registra um caso muito importante:

> `CORE-MAPPING.md` classificava `Orchestrator.ts` como MOCK, mas a auditoria posterior descobriu que ele é um pipeline real de 14 passos.

Ou seja:

**até os documentos de auditoria podem estar errados.**

Isso deveria virar uma regra permanente do Execution Plan:

```text
DOCUMENTAÇÃO ≠ EVIDÊNCIA

Toda afirmação de estado:
REAL / READY / IMPLEMENTED / WORKING
deve possuir uma evidência verificável:

- ficheiro + linha
- teste
- execução real
- CI
- query
- commit
- artefacto

Se não houver evidência:
status = UNVERIFIED
```

Isso é muito mais forte do que simplesmente “evidência ficheiro:linha”.

---

# 5. Falta formalizar “UNVERIFIED”

Hoje você tem:

```text
ready
partial
gap
```

Eu acrescentaria:

```text
verified
partial
unverified
gap
blocked
deferred
```

Porque:

**gap ≠ unverified.**

Exemplo:

```text
L5
```

não parece ser um gap.

Existe.

O problema é saber se a versão atual está funcionando conforme esperado.

Então:

```text
L5 = partial / unverified
```

é muito mais preciso do que:

```text
L5 = gap
```

---

# 6. Falta uma camada de avaliação do próprio sistema

Você colocou retrieval evaluation em F3, o que está correto.

Mas eu ampliaria para uma seção permanente:

## Evaluation & Quality

Porque nas auditorias do Git já apareceram:

* DeepEval;
* Ragas;
* coverage;
* replay;
* testes determinísticos;
* comparação estimated vs actual;
* avaliação de retrieval.

O objetivo não deve ser apenas:

> “o sistema funciona?”

Mas:

```text
Capability
   ↓
functional test
   ↓
quality test
   ↓
cost test
   ↓
security test
   ↓
regression test
   ↓
evidence
```

Isso será fundamental para o seu objetivo de **padrão ouro**.

---

# 7. O plano também precisa incorporar explicitamente o problema de T6

Você já possui:

`docs/T6-INGEST-PIPELINE.md`

E ele define algo muito importante:

> Git = source of truth; RAG = índice derivado.

Isso é uma decisão arquitetural excelente e deveria aparecer no Execution Plan.

Porque, caso contrário, F1/F3 podem inadvertidamente construir **um segundo mecanismo de ingestão**.

Eu adicionaria:

```text
REGRA T6

Git = source of truth
L5/RAG = derived index

Toda ingestão deve ser:
- idempotente
- incremental
- hash-based
- capaz de purge
- auditável
- reproduzível
```

E principalmente:

> **F1 não cria um novo pipeline paralelo. O MarkItDown deve alimentar o pipeline T6/L5 existente.**

Isso está implícito no seu documento, mas eu tornaria explícito.

---

# 8. Está faltando o “contract-first” como regra transversal

Você já está fazendo isso, mas o documento ainda não transforma isso numa regra.

Eu adicionaria:

```text
Toda nova primitive/capability/tool deve possuir:

1. Contract
2. Input schema
3. Output schema
4. Policy
5. Provenance
6. Error states
7. Validation
8. Observability
9. Cost/budget behaviour
10. Security boundary
```

Isso é particularmente importante para:

* MarkItDown;
* Crawl4AI;
* OSV;
* Instructor;
* futuras tools;
* Execution Broker.

Assim vocês não criam apenas “scripts que funcionam”.

Criam **primitives com contrato**.

---

# 9. Multi-worker: a ideia está boa, mas eu moveria “5 budgets”

A seção do Broker está boa conceitualmente.

Mas eu não congelaria ainda a estrutura:

```yaml
session
plan
task
providers
```

como se já fosse contrato final.

Porque antes vocês precisam decidir:

```text
budget
quota
rate limit
availability
cost
authorization
quality requirement
```

são conceitos diferentes.

Eu escreveria:

> **Modelo preliminar — não contrato v1.**

E acrescentaria:

```text
availability ≠ quota
quota ≠ budget
budget ≠ cost
authorization ≠ capability
capability ≠ quality
```

Essa distinção vai evitar uma confusão enorme quando vocês implementarem o Broker.

---

# 10. O Execution Lease merece uma regra de segurança que ainda não está explícita

O Lease deveria ter:

```text
lease_id
task_id
holder
capabilities
permissions
budget
issued_at
expires_at
status
revoked_at?
revoked_reason?
```

E uma regra:

> **Lease expirado ou revogado não pode executar.**

Além disso:

```text
1 task
1 active lease
```

como invariável.

Isso transforma o Lease de uma ideia de concorrência numa verdadeira **fronteira de autorização operacional**.

---

# 11. Falta “idempotência” na parte de execução

Você já tem isso implicitamente em ingestão, mas precisa existir no Execution Plan inteiro.

Imagine:

```text
Grok executou
↓
resposta chegou
↓
rede caiu
↓
runner não recebeu ACK
↓
retry
```

Sem idempotência:

**executa duas vezes.**

Então eu acrescentaria:

```text
Toda capability mutável deve declarar:
- idempotency key
- retry policy
- side effects
- rollback/compensation quando possível
```

Especialmente para o futuro:

* GitHub write;
* produção;
* financeiro;
* trading;
* CRM;
* manufacturing.

---

# 12. Falta separar claramente READ / PREPARE / ACT

Isso aparece em Security, Trading etc., mas deveria ser Universal Core.

Eu colocaria uma taxonomia:

```text
READ
↓
PREPARE
↓
ACT
```

com políticas:

```text
READ:
pode ser automático

PREPARE:
pode exigir policy/HITL dependendo do domínio

ACT:
privileged capability
+ authorization
+ explicit policy
+ audit
+ HITL quando exigido
```

Isso será extremamente importante para o futuro Broker.

---

# 13. Legal/Medicine/Trading não deveriam entrar apenas como “domínios futuros”

O raciocínio está correto, mas eu adicionaria uma regra de **readiness gate**.

Por exemplo:

### Legal

Não pode virar `ready` sem:

```text
jurisdiction
source authority
effective dates
version
provenance
HITL
```

### Medicine

Não pode virar `ready` sem:

```text
source
guideline version
publication date
clinical provenance
scope
HITL
```

### Trading

Não pode virar `act` sem:

```text
market data provenance
risk controls
backtesting
position limits
authorization
HITL
audit
```

Isso impede que daqui a seis meses alguém veja:

```text
medicine/
knowledge/
skills/
```

e conclua:

> “Medicine está pronta.”

---

# 14. Falta incluir explicitamente “Source Authority”

Você colocou `authority?`, ótimo.

Mas eu faria disso uma dimensão própria do L5:

```text
source
authority
jurisdiction
validity
version
retrieval_time
```

Porque:

```text
"quem publicou?"
```

é diferente de:

```text
"qual autoridade tem essa fonte?"
```

E isso será fundamental para Legal, Medicine, normas técnicas, segurança e finanças.

---

# 15. Falta uma regra para conflitos entre fontes

Este é um dos maiores gaps de Knowledge Engineering que ainda não está suficientemente explícito.

Imagine:

```text
Fonte A
versão 2025

Fonte B
versão 2026

Fonte C
revogada
```

O L5 não pode simplesmente retornar os três chunks e deixar o LLM decidir.

Precisamos futuramente de:

```text
source precedence
version
effective_from
effective_until
supersedes
superseded_by
jurisdiction
authority
```

E uma regra:

> **retrieval relevante não significa retrieval válido.**

Eu colocaria isso no F3 como **Knowledge Validity / Conflict Resolution**.

Não precisa implementar agora.

Mas precisa estar no plano para não se perder.

---

# 16. Falta explicitamente “Deletion / Revocation”

O provenance está muito focado em adicionar informação.

Mas conhecimento também:

* expira;
* é revogado;
* é substituído;
* é removido;
* deixa de ser aplicável.

O contrato deveria prever:

```text
active
superseded
revoked
expired
deleted
```

Isso conversa diretamente com o seu L4 `supersedes`.

---

# 17. O “Domain Onboarding Cost” merece virar KPI formal

Você chamou de indicador, mas eu faria dele uma métrica real.

Por exemplo:

```text
DOC =

core files modified
+
core code changes
+
new infrastructure
+
new runtime
+
new persistence
+
new orchestration logic
```

O objetivo:

```text
DOC(core changes) = 0
```

para um Domain Pack normal.

E outro KPI interessante:

### Reuse Ratio

```text
Universal capabilities reused
--------------------------------
Total capabilities required
```

Isso mede se a plataforma realmente é universal ou apenas está acumulando agentes.

---

# 18. Falta uma regra de “capability maturity”

Hoje:

```text
YAML → capability
```

é insuficiente, e vocês já perceberam isso.

Eu criaria:

```text
DRAFT
↓
DECLARED
↓
WIRED
↓
EXECUTABLE
↓
VALIDATED
↓
PROVEN
```

Exemplo:

```text
security.defensive_audit
PROVEN
```

se existe evidência E2E.

Enquanto:

```text
marketing.analytics
DECLARED/GAP
```

não deve ser tratado como capability pronta.

Isso combina perfeitamente com o E7.

---

# 19. Falta “sunset / deprecation”

Como o objetivo é evoluir para sempre, também precisamos decidir quando algo **deixa de existir**.

Especialmente:

* skills duplicadas;
* agentes antigos;
* adapters;
* ferramentas;
* frameworks experimentais;
* conhecimento obsoleto.

Adicionar:

```text
deprecated_at
replacement
reason
migration
```

evita que o projeto cresça indefinidamente.

---

# 20. E existe uma regra documental que eu considero obrigatória

Você escreveu:

> “o que este documento não cobrir, não existe.”

Eu manteria, mas acrescentaria:

> **O documento não é uma segunda fonte de verdade do estado operacional.**

Porque senão você cria exatamente outro problema de sincronização.

Eu faria:

```text
ARCHITECTURE
    EXECUTION-PLAN.md
        ↓
DECISIONS
    ADRs
        ↓
WORK
    OPEN-ITEMS.md
        ↓
EVIDENCE
    commits / tests / CI / reports
        ↓
CURRENT STATUS
    STATUS.md
```

E o Execution Plan contém:

**o que deve acontecer e por quê.**

O OPEN-ITEMS contém:

**o que ainda falta.**

O Git/CI contém:

**o que realmente aconteceu.**

---

# Minha avaliação final

O documento que você montou já captura **a espinha dorsal correta**.

Mas, para o objetivo que você colocou — **“algo único, um plano de execução, sem deixar nada perdido, padrão ouro”** — eu faria uma **Parte 4 curta**, não outra grande matriz.

Ela seria:

## 14. GOVERNANÇA DO PRÓPRIO EXECUTION PLAN

Com apenas estes blocos:

```text
14.1 Fonte de verdade e hierarquia documental
14.2 Regra de evidência
14.3 Estados: verified / partial / unverified / gap / blocked / deferred
14.4 Contract-first
14.5 READ / PREPARE / ACT
14.6 Idempotência e retry
14.7 Capability maturity
14.8 Knowledge validity / conflicts / revocation
14.9 Domain Onboarding Cost + Reuse Ratio
14.10 Deprecation / sunset
14.11 Regra de atualização do próprio plano
```

E eu faria **duas correções no conteúdo existente**:

### Correção A — F0

Trocar:

> “provar L5 porque não está verificado”

por:

> **“revalidar a implementação L5 já existente, confirmar estado canónico atual, cobertura Security e medir retrieval.”**

Porque o Git mostra evidência de C8.

### Correção B — Security

Trocar:

> “Security 100% fechada”

por:

> **“SEC-1/SEC-2 fechados; Security Domain Pack ainda possui capabilities parciais/deferred e aguarda validação L5/E2E.”**

---

## E há uma terceira coisa que eu faria antes de entregar ao Claude

**Não mandaria ainda “grava e começa F0”.**

Primeiro mandaria:

> **“Integra a Parte 4 de governança do próprio plano e corrige F0/estado Security conforme a auditoria do repo. Não implementar nada. Depois apresenta o documento final consolidado para revisão.”**

Só depois de termos o **EXECUTION-PLAN.md final** eu daria:

> grava → OPEN-ITEMS → F0.

Isso evita que o primeiro documento oficial já nasça com a ambiguidade L5 e com algumas decisões importantes apenas implícitas.

E, olhando o Git atual, essa pequena etapa extra é justificável: **já existe muita coisa boa no repositório, mas também existem documentos históricos, auditorias que corrigem auditorias anteriores e componentes reais que foram classificados incorretamente.** O padrão ouro precisa incluir justamente um mecanismo para não voltar a cair nesse problema.
