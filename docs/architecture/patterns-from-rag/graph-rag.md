# Graph RAG — quando vale a pena

## RAG vector pergunta

“Quais *passagens* são semanticamente parecidas com a query?”

## Graph RAG pergunta

“Quais *entidades* ligam este assunto e que documentos sustentam essas arestas?”

Exemplo jurídico:

```text
Cliente --possui--> Processo --junto_a--> Conservatória
                         |
                    fundamentado_em
                         |
                       Norma / Artigo
```

## Quando usar

| Sim | Não (ainda) |
|-----|-------------|
| Relações estáveis (partes, órgãos, produtos, vias de cidadania) | Corpus pequeno e FAQs planas |
| Queries multi-hop (“quem trata X ligado a Y”) | Só “o que diz o PDF sobre Z” |

## Stack de referência

LightRAG / GraphRAG + store (Neo4j ou grafo embutido) **em paralelo** ao Qdrant, não em substituição no dia 1.

## Integração agents

Tool separada `retrieve_graph` vs `retrieve_vector`; orchestrator escolhe ou híbrido no RAG service.
