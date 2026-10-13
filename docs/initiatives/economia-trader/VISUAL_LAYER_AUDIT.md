# Auditoria da camada visual — economia-trader

**Data:** 2026-10-13  
**Âmbito:** auditoria read-only do código presente em `main` e do PR #190 merged. Não houve execução visual real nesta auditoria.

## Veredito executivo

**Recomendação A: manter o painel HTML próprio como interface operacional principal; manter Star-Office-UI apenas como visualização opcional, atrás de um processo separado, até substituir os assets não comerciais.** Não adotar um terceiro frontend agora. O painel já existe e é alimentado pelos ficheiros de estado/diário do trader; criar outra interface antes de validar o contrato de eventos duplicaria trabalho.

## Evidência da implementação existente

- `oss/economia-trader/src/economia_trader/dashboard.py`: página HTML estática, construída a partir de `state.json`, `journal.jsonl` e `events.jsonl`; não precisa de servidor nem de dependência JS para a visualização.
- `oss/economia-trader/src/economia_trader/office.py`: ponte separada que lê o diário e envia estados ao Star-Office-UI. Os cinco papéis mapeados são monitor, triagem, analista, risco e executor.
- PR [#190](https://github.com/souzalrns/network-agents-setup/pull/190) está **merged**; a descrição reporta 83 testes e validação visual em 1100 px e 390 px. Isto é evidência reportada pelo PR, não uma execução independente nesta auditoria.
- O código de Star-Office-UI é declarado MIT no PR, mas a própria implementação documenta que os assets gráficos são **não comerciais**. Para uso comercial, substituir os assets por arte própria ou por assets com licença comercial verificável.

## Verificação da fronteira evento real vs. animação

A ponte traduz eventos do diário em estados visuais. Exemplos no código:
- `proposal` → triagem a executar;
- `opinion`/`forecast` → analista a escrever ou em erro/veto;
- `assessment`/`blocked`/`auto_kill` → estado do módulo de risco;
- `intent`/`order`/`fill` → executor;
- `run` → monitor.

Isto dá uma base causal verificável. Contudo, o estado do avatar é uma **projeção resumida do último evento**, não prova de que um agente está atualmente ocupado nem telemetria contínua do processo. A UI deve mostrar timestamp, origem do evento e idade do estado; ausência de evento deve aparecer como “sem atualização”, nunca como atividade inventada. Dados sintéticos têm de trazer rótulo DEMO.

## Alternativas visuais consideradas

| Candidato | Adequação | Limitação/risco | Decisão |
|---|---|---|---|
| Painel HTML próprio (`dashboard.py`) | Alta para estado financeiro, decisões, risco, diário e mobile; usa artefactos reais | Não é uma sala pixel-art nem uma consola multiusuário em tempo real | **A — manter como fonte operacional** |
| Star-Office-UI + ponte `office.py` | Alta para representar papéis/estados dos agentes; já integrado | Assets não comerciais; estado é resumo do diário; serviço visual externo tem de ser isolado | **B — opcional, trocar assets antes de uso comercial** |
| PixelFloor (`fumeilab/pixelfloor`) | Conceito próximo de sala pixel-art e integração backend por eventos | Não foi possível confirmar nesta auditoria a licença e o contrato de eventos a partir de uma revisão completa dos ficheiros do projeto | Não adotar sem auditoria de código/licença |
| Agent Office (`Doc-Code/agent-office`) | Conceito de escritório de agentes em tempo real | Não verificados aqui todos os ficheiros de licença, origem de assets e protocolo; exige nova avaliação antes de comparação final | Não adotar agora |
| Agent Visualizer for LangChain (`coderonfleek/agent-visualizer-langchain`) | Observabilidade de fluxo de agentes | Orientado a LangChain e não a um chão de negociação; integração e licença devem ser confirmadas no commit candidato | Não adotar agora |

**Limite de confiança:** as três alternativas externas acima são triagem de candidatos, não auditoria legal completa. Não foram tratadas como aprovadas para reutilização comercial.

## Requisitos de aceitação para a próxima melhoria visual

1. Cada mudança visual tem de apontar para evento/identificador no diário ou ser explicitamente DEMO.
2. Mostrar modo (`paper`, `testnet`, `live`), kill switch, timestamp de atualização e aviso de dados desatualizados.
3. Não expor chaves, tokens, payloads secretos ou detalhes sensíveis nos textos enviados ao escritório.
4. Falha ou indisponibilidade da camada visual nunca pode bloquear, atrasar ou autorizar uma ordem.
5. Não utilizar os assets não comerciais em distribuição comercial; substituir e documentar licença antes disso.

## Conclusão

Não falta construir um painel de raiz. Falta concluir a decisão de licenciamento dos assets, validar a semântica dos estados em uso real e melhorar a indicação de frescura/origem. A ação de menor risco é manter o painel existente e tratar o escritório como plugin visual não autoritativo.
