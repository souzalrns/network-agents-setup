# Porque eu escolheria o auditron (e quando não)

> Exercício pedido pelo maestro: chegar ao fim e dizer, com honestidade, se eu escolheria este
> projecto frente às alternativas — e porquê. Sem reputação nem estrelas a pesar na balança.

## O problema real

`pip-audit`, `bandit` e `zizmor` são três ferramentas maduras e excelentes. Ninguém precisa de outra
ferramenta de análise. O que falta, em quase todos os repos, é a **cola**: instalar três coisas,
lembrar três comandos e três formatos de saída, decidir o que bloqueia o CI e o que só informa, e
juntar tudo num sítio que a aba Security do GitHub entenda. Essa cola costuma virar um `.sh` copiado
de repo em repo, que ninguém testa e que apodrece.

## O que o auditron é (e o que não é)

- **É** um orquestrador fino: um `pip install`, um `auditron scan`, uma política (`auditron.toml`),
  um relatório (JSON + SARIF 2.1.0), um código de saída. Nada mais.
- **Não é** um motor de análise novo. Não reimplementa SAST nem SCA. Se o `bandit` melhorar, o
  auditron melhora de graça.
- **Não é** ofensivo. Só lê e relata. Pentest e red-team de LLM são companheiros de laboratório,
  documentados, fora do pacote.

## Comparação honesta

| Alternativa | Vantagem dela | Porque o auditron ainda ganha para este caso |
|---|---|---|
| **Um `.sh` à mão no CI** | zero dependências novas | não tem modelo comum, nem SARIF, nem testes; a lógica de "o que bloqueia" vive no YAML e duplica-se por repo |
| **pre-commit com os 3 hooks** | ecossistema conhecido | é por-ficheiro no commit, não um gate de repo com política e SARIF agregado; não unifica a saída |
| **Scanner hospedado (SaaS)** | dashboards, histórico | custo, e manda o código para fora — contra a premissa custo zero e a privacidade; o auditron corre no runner do próprio repo |
| **Megaferramenta tudo-em-um** | cobre mais linguagens | peso e configuração; o auditron fica propositadamente pequeno e previsível, com 3 engines que já usamos |

## Quando NÃO escolher o auditron

- Se o repo não é Python e não tem GitHub Actions, sobra só o `pip-audit` — não vale a camada.
- Se já tens um SAST multilinguagem hospedado e pago que a equipa usa, o auditron só duplicaria.
- Se precisas de análise profunda entre ficheiros (dataflow, taint) — isso é CodeQL/semgrep, que
  ficam a par, não dentro, do auditron.

## A escolha

Para um ecossistema de **repos pequenos de agentes, Python + Actions, custo zero e privados**, eu
escolheria o auditron: é a peça que torna a segurança defensiva **um comando acoplável**, testado,
reproduzível (versões fixadas em cada relatório) e pronto a sair para o seu próprio repositório sem
uma linha de mudança — tal como o `skill-scout`. A disciplina é a característica, não a quantidade de
engines: começa pequeno, bloqueia só o que é factual (CVEs), e promove o resto a bloqueante quando o
repo faz a triagem. É o que eu quereria "acoplar e esquecer".

**Não** o escolheria como ferramenta única de uma empresa multilinguagem com orçamento de segurança —
aí é um complemento, não o centro. A honestidade faz parte do padrão ouro.
