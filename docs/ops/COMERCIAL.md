# Pack Comercial (COM-1)

> Decisão do maestro (2026-10-24, **D2 = A**): o primeiro bloco do ciclo operacional que faltava
> (pedido → venda → entrega → faturação → relatório) é o **Comercial**. Origem: a comparação com o
> agents-office do ajsahni (o departamento Sales dele tinha propostas, follow-ups e inbound; nós só
> tínhamos prospeção, ofertas, preços, sales_enablement e revops).

## O que entra

| Lugar no escritório | Agente | Action | Skill | O que entrega |
|---|---|---|---|---|
| LEADS INBOUND | `marketing.inbound_qualification` | `lead_qualification` | `skills/marketing/lead_qualification/SKILL.md` | Classificação (quente/morno/frio/fora de âmbito) com a frase do pedido como evidência, resposta proposta e próxima acção |
| PROPOSTAS | `marketing.proposals` | `proposal` | `skills/marketing/proposal/SKILL.md` | Proposta com âmbito incluído e excluído, preços só da tabela do plano, lacunas `[[A DEFINIR]]` e email de envio |
| FOLLOW-UPS | `marketing.follow_ups` | `follow_up` | `skills/marketing/follow_up/SKILL.md` | Pipeline classificado (em dia/follow-up/fechar/parar) e rascunhos com um motivo novo cada |

Os 3 juntam-se, no departamento **Comercial** do escritório, a `prospecting`, `cold_email`, `offers`, `pricing`, `product_marketing`, `sales_enablement` e `revops`.

## Regras que não se dobram

- **Nada é enviado, respondido ou marcado.** `act_in_production: forbidden`; o plano acaba sempre num gate `plan_approve`. As capabilities são só `read`/`prepare`.
- **Nunca inventar** preço, prazo, desconto, garantia ou referência de cliente. Sem dados, fica `[[A DEFINIR]]` e vai para "Lacunas".
- **Orçamento e decisor só se o pedido os disser.** Deduzir da morada, do email ou da profissão é proibido.
- **Quem pede para parar sai da lista** (RGPD art. 21.º; LGPD art. 18.º).
- **Dados pessoais:** só os do pedido ou do pipeline, só para responder (RGPD art. 6.º, n.º 1, al. b); LGPD art. 7.º, V). Num run real, pedido e pipeline entram pelos `inputs` e nunca vão para o git.
- **Sigilo profissional** (ex.: ViannaLegal): não copiar factos do caso para além do necessário; um pedido jurídico urgente vai sempre para o humano.

## Demo

`docs/orchestration/marketing/templates/examples/comercial-demo.plan.yaml`: qualificar → proposta → follow-ups → gate. A fixture (`fixtures/comercial-pedido-ficticio.md`) é toda **fictícia**: pedido, tabela de preços e pipeline (com um cliente que pediu para parar, para provar a regra).

```bash
cd runner
python -m plan_runner run ../docs/orchestration/marketing/templates/examples/comercial-demo.plan.yaml --mode stub --out ../pilots/run-comercial
python -m plan_runner run ... --mode external --worker gemini --out ../pilots/run-comercial   # run real: GEMINI_API_KEY do maestro
```

Testes: `runner/tests/test_com1_comercial_pack.py` (E7, capabilities sem execução, contrato das skills, plano só com dados fictícios, stub até ao gate e o Comercial "precisa de ti" no escritório).

## Router (o que NÃO mudou, e uma decisão para o maestro)

- Os 3 agentes entram na área `marketing` de `config/areas.yaml` sem keywords novas. Este é o router do **runner** (`plan_runner/router.py`); o conector do Claude.ai usa o router do `agent-network-mcp`, que não lê este ficheiro.
- Pelo router do runner, um pedido que diga só "proposta" ou "follow-up" não casa com nenhuma área e vai para a área de fallback (`horizontal`, o planeador); pelos planos (o caminho principal), as actions chegam directamente aos agentes.
- **Ambiguidade antiga:** `orcament` está na área `finance`. "Pedido de orçamento" de um cliente (comercial) vai hoje para Finanças.
- Decisão a propor no §10 do PENDENCIAS: juntar keywords comerciais à área `marketing` e tratar "orçamento" no sentido comercial.

## Fora deste pack (registado)

- Integração com o email, com um CRM ou com um calendário: cada uma é uma decisão própria (custo, sigilo, credenciais).
- Os outros blocos do ciclo: Caixa de entrada, Entrega ao cliente, Finanças operacionais, Relatórios internos e Compliance.
