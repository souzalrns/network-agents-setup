# Strix — piloto de pentest em laboratório (SEC-STRIX-1, P-47 = A)

> Capability `external_pentest_lab` (`config/security-capabilities.yaml`), nível **lab**, `status: deferred`.
> **Fora do runner de produção.** A política da área `security` não muda: `offensive: forbidden`,
> `act_in_production: forbidden`, `hitl: required`. O Strix só corre no CI, à mão, contra repos próprios.

## 1. O que é

[Strix](https://github.com/usestrix/strix) (Apache-2.0) é um pentester de IA: corre a aplicação,
procura falhas estilo OWASP (injecção, XSS, SSRF, IDOR, bypass de auth, JWT) e **confirma cada uma
com uma prova de conceito**. É ofensivo por natureza — é o que o distingue da nossa auditoria
defensiva (`meta.security-auditor`, que só lê e relata).

Cobre a lacuna real da área: hoje temos triagem, auditoria defensiva, gitleaks, semgrep e CodeQL,
mas nenhum teste dinâmico que **confirme** uma falha. O Strix não substitui a auditoria defensiva;
é um segundo olhar, de laboratório.

## 2. Regras do piloto (não negociáveis)

- **Só repos próprios e com autorização.** O alvo da v1 é o **NAS** (`network-agents-setup`), que é
  público. O **ANM é privado**: apontá-lo ao Strix manda o código ao fornecedor do LLM e exige uma
  decisão à parte do maestro antes de qualquer run.
- **Nunca no runner de produção nem num plano.** A capability fica `deferred`/`lab`; o E7 recusa o
  nível `lab` fora de `deferred`.
- **Nunca em produção nem contra terceiros.** Sem URLs de produção, sem sistemas que não sejam nossos.
- **Manual.** O workflow é `workflow_dispatch` e **nunca bloqueia** (`continue-on-error`). Não corre
  em `push` nem em `pull_request`.
- **Modelo fixado, custo medido.** A premissa é custo zero: o run usa o Gemini Flash Lite e mede os
  tokens antes de qualquer compromisso. Nunca usar o modelo por omissão do Strix (OpenRouter).
- **Segredos.** A chave do LLM vem de `secrets.LLM_API_KEY` (o DEV põe-na nas repo secrets). Sem o
  segredo, o workflow não corre (sai 0, sem erro). A chave nunca aparece em logs nem no git.

## 3. Como correr (DEV)

1. Pôr `LLM_API_KEY` nas **Settings → Secrets → Actions** do `network-agents-setup`.
2. Actions → **strix-lab** → *Run workflow*, com:
   - `strix_version`: a versão do pacote `strix-agent` no PyPI (fixada; não usar tag móvel);
   - `strix_llm`: o id do Gemini Flash Lite que o Strix aceita (litellm; confirmar o id actual);
   - `target`: `.` (o código do repo) por omissão;
   - `scan_mode`: `quick` por omissão.
3. No fim, descarregar o artefacto `strix-lab-run` (o `strix_runs/`) e ler o relatório.

O job corre em Docker, no runner do GitHub (repo público, minutos grátis).

## 4. O que o piloto mede

Preencher depois do 1.º run (evidência para decidir se passa de `deferred`):

| Métrica | Como | Resultado |
|---|---|---|
| Tokens / custo | somatório do run com Gemini Flash Lite | — |
| Falhas confirmadas (com PoC) | relatório do Strix | — |
| Falsos positivos | revisão humana (HITL) | — |
| Tempo do job | duração no Actions | — |
| Sobreposição com semgrep/CodeQL | comparar achados | — |

## 5. Critérios de saída do piloto

- **Promover** (abrir decisão para tirar o `deferred`): se encontrar falhas reais que o semgrep/CodeQL
  não apanham, com poucos falsos positivos e custo dentro do tier gratuito.
- **Manter em lab manual:** se for útil mas caro ou ruidoso — corre só quando o DEV o lança.
- **Descartar:** se não acrescentar nada ao que já temos.

A decisão de promover é do maestro (nova entrada em §10 do `PENDENCIAS.md`), com a tabela do §4 preenchida.

## 6. Riscos registados

- **Privacidade:** o Strix envia o código ao fornecedor do LLM. Aceitável no NAS (público); no ANM
  (privado) exige decisão do maestro. Ver a política de privacidade (GOV-IMPACT-1) e a ISO 42001 (P-40).
- **Supply chain:** instalar pelo pacote `strix-agent` do PyPI com versão fixa, nunca pelo `curl | sh`.
- **Âmbito:** o modo ofensivo contra o alvo errado é um incidente. Daí o alvo fixo (o próprio repo) e
  o workflow manual.
