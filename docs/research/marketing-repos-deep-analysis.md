# Análise profunda — fontes marketing agents (2026-09)

Fontes pedidas:

1. https://github.com/asv-digital/agents-agencia-marketing  
2. https://github.com/topics/digital-marketing-agency?o=desc&s=updated  
3. https://github.com/topics/social-media-marketing?o=desc&s=updated  

Fontes adjacentes de alto sinal (tópico / search):

- [digital-marketing-pro](https://github.com/indranilbanerjee/digital-marketing-pro) — OS de marketing com skills + agents + metodologia  
- [agency-agents-pt-BR](https://github.com/jnMetaCode/agency-agents-pt-BR) — biblioteca de personas (incl. marketing)

---

## 1. asv-digital/agents-agencia-marketing

### O que é de facto

Repositório com **~57 pacotes `.zip`**, um por “agent/processo”. Título: *57 agents Claude Code para gerenciar agência*.

**Não** é um runtime multi-agente (sem orchestrator, sem MCP, sem plan-execute). É uma **biblioteca de playbooks operacionais de agência** empacotados para uso com Claude Code / prompts.

### Taxonomia dos 57 (agrupada)

| Bloco | Exemplos (nº no repo) | Natureza |
|-------|----------------------|----------|
| **Comercial / new business** | 01 prospecção LinkedIn, 02 audit isca, 03 discovery, 04 RFP, 05 proposta, 06 precificação, 07 pitch, 08 contrato | Vendas + jurídico comercial |
| **Onboarding cliente** | 09 brief, 10 kickoff, 11 30-60-90, 12 acessos/credenciais, 13 SLA | Account start |
| **Delivery / PM** | 14 account plan, 15 squad, 16 sprint 2 sem, 17 daily, 18 status report, 19 tracking tarefas, 20 timesheet, 21 capacity, 22 escalation | Ops de projecto |
| **Governança cliente** | 23 reunião mensal, 24 QBR, 25 ata, 26 newsletter resultados, 27 deck, 28 follow-up | Cadência cliente |
| **Criação** | 29 brief interno, 30 aprovação 3 rodadas, 31 creative library, 32 review criativo, 33 naming/versionamento, 34 handover entrega | **Core criativo** |
| **Financeiro** | 35–40 margem, BDI, cobrança, inadimplência, forecast MRR | Admin financeiro |
| **People** | 41–46 hiring, freelancer, onboarding staff, carreira, 1:1, retenção | RH |
| **Retenção / growth account** | 47–51 NPS, churn, win-back, upsell, case sucesso | CS / comercial |

(Lista no GitHub continua além do 51 no mesmo padrão de zips.)

### O que roubar

| Padrão | Valor para o nosso setup |
|--------|---------------------------|
| **Mapa completo do ciclo de vida da agência** | Completa gaps de *processo* (brief → aprovação → handover) |
| **Brief interno + 3 rodadas de aprovação** | HITL multi-round explícito |
| **Review criativo padronizado** | Critic com rubrica |
| **Naming/versionamento de ficheiros** | Artefactos L2 previsíveis |
| **Sprint marketing 2 semanas** | Template de plan recorrente |
| **Status report / QBR como deliverable_type** | Novos templates de plan |
| **SLA + escalation matrix** | Policy + on_fail / human |
| **Creative library** | L5 knowledge de referências (não admin) |

### O que **não** adoptar por inteiro

| Item | Motivo |
|------|--------|
| Zips binários como dependência | Frágil, pouco auditável, licença/conteúdo opaco no browse |
| Financeiro / RH / timesheet / cobrança | Fora do scope “sem área administrativa” da vertical marketing cognitiva |
| Contrato/precificação como agent core | Legal/comercial humano; no máximo template de *texto* com HITL forte |
| Credenciais handover | Risco de segurança; nunca skill que peça passwords em plain |
| “57 agents” = 57 runtimes | São playbooks; mapear a **actions/templates**, não a 57 processos LLM paralelos |
| Clonar repo como submodule | Preferir **reescrita** de padrões no nosso formato plan/skill |

### Veredicto ASV

**Ingerir:** taxonomia de processos + padrões de brief/aprovação/review/sprint/report.  
**Adoptar por inteiro:** **não** o repositório.  
**Implementar:** como `deliverable_type` + skills de *processo criativo/account delivery*, não como admin stack.

---

## 2. Topic `digital-marketing-agency`

Amostra recente (ordenado por updated): maioria **sites de agência**, temas Astro, SEO audit scripts, link shortener, SMM panels duvidosos.

### Sinal útil

| Repo / tipo | Roubar? |
|-------------|--------|
| SEO technical audit toolkits (crawl, metadata, canonicals) | **Sim** como tools/skills de auditoria (L5 + action `seo_tech_audit`) |
| Marketing suite dashboards (Next.js client mgmt) | Só UX ideas; não core agents |
| Temas site agência (Positivus, etc.) | Não (front) |
| SMM panels / “tiktok coins” | **Não** (spam / ToS / ética) |

### Veredicto topic DMA

Baixa densidade de *multi-agent systems*. Ouro = **SEO audit automation** e checklists técnicos, alinhados ao Item 13 + seo_brief.

---

## 3. Topic `social-media-marketing`

(Fetch parcial/instável.) Em geral: calendários, bots de post, painéis SMM, growth hacks.

### Roubar

- Calendário editorial como artefacto (`content_calendar`)  
- Variantes por canal (já no template social_pack)  
- UGC/influencer brief structure  

### Não adoptar

- Auto-post sem HITL  
- Engagement pods / fake growth  
- Credenciais de redes em skills  

---

## 4. digital-marketing-pro (alto sinal, adjacente)

Sinais públicos do projecto:

- Dezenas/centenas de **skills** + **specialist agents**  
- Metodologia explícita (strategy flow com muitos steps)  
- Brand context + **human approval** + outputs verificáveis  
- AEO/GEO além de SEO  
- Multi-brand state  
- Compliance (ex. disclosure)  

### Roubar / alinhar

| Padrão | Nosso equivalente |
|--------|-------------------|
| Metodologia step-by-step auditável | plan.yaml + done_when |
| Brand context pack | L4 project + L5 brand kit |
| Human approval | human_gate |
| AEO/GEO | Item 13 (já) |
| Skills granulares | L3 SKILL.md + registry |
| Multi-brand | scope `project` |
| Verifiable outputs | schemas + critic |

### Não adoptar por inteiro

Lock-in a um plugin de um IDE; CRM admin completo; 163 skills de uma vez (ingestão selectiva).

---

## 5. agency-agents (personas)

Biblioteca de **personas** (marketing ~30, paid media, etc.).

### Roubar

- Roster de papéis para completar gaps (Growth, Reddit, Programmatic…)  
- Formato: identidade + regras críticas + entregáveis  

### Não adoptar por inteiro

187 agentes no runtime; personas sem plan-execute = prompt soup.

---

## 6. Matriz final: roubar / ingerir / adoptar

| Item | Roubar padrão | Ingerir conhecimento | Adoptar por inteiro |
|------|---------------|----------------------|---------------------|
| ASV taxonomia processos | ✓ | ✓ (lista + mapeamento) | ✗ repo/zips |
| ASV brief + 3 aprovações + review | ✓ | ✓ regras | como templates |
| ASV sprint / status / QBR | ✓ | ✓ | templates opcionais |
| ASV finanças/RH/credenciais | ✗ | ✗ | ✗ |
| SEO audit tools (topic) | ✓ | checklist | tool/action |
| SMM auto-growth panels | ✗ | ✗ | ✗ |
| digital-marketing-pro method | ✓ | selectivo | ✗ monólito |
| agency-agents personas | ✓ gaps de role | prompts adaptados | ✗ 187 runtime |
| Nosso runner + orchestrator | — | — | **sim, continuar** |

---

## 7. Providências adoptadas neste repo

Ver:

- `docs/orchestration/marketing/PROVIDENCIAS-ADOTADAS.md`  
- templates adicionais  
- extensão do registry de actions  
