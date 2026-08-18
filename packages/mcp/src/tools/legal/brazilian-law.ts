// packages/mcp/src/tools/legal/brazilian-law.ts
//
// NOTA DE FIDELIDADE: o material colado pelo usuário só tinha um rascunho comentado desta
// função (Fase 1.2 do plano de "INGESTÃO INICIAL"), com ferramentas chamadas
// "ingest_legislation_br" / "ingest_jurisprudence_br" / "ingest_doctrine_br" cujo corpo
// era só comentários (`// 1. Busca no Planalto`, `// 2. Extrai conteúdo`, etc.) e um
// `return { success: true, documentId: '...' }` fixo — pseudocódigo, não implementação.
//
// A ingestão de verdade (scraping + upsert no Postgres) já existe em
// packages/scripts/src/ingest/brazilian-law.ts, rodando como job em lote (scripts/cron),
// não como uma tool MCP chamada por um agente durante uma conversa — scraping é lento,
// sujeito a rate-limit e não deveria travar uma resposta de chat. Por isso, as ferramentas
// aqui foram reorientadas para o que um agente jurídico realmente precisa em tempo real:
// consultar o que já foi ingerido em LegalDocument (busca e leitura), seguindo o mesmo
// padrão dos outros built-in tools deste pacote (createDatabaseTools, createWebTools).

import { MCPTool } from '../ToolRegistry';
import { prisma } from './db';

// Amostra fixa usada só quando a base ainda não tem NENHUM documento BR ingerido (ex.:
// antes da primeira `pnpm ingest` rodar) — para o agente não receber "0 resultados" e
// achar que a capability está quebrada, e sim ver que a estrutura de resposta funciona.
// Sempre marcada com `source: 'simulated'`, nunca confundida com um resultado real.
const SIMULATED_BR_LAWS = [
  {
    title: 'Lei 10.406/2002 - Código Civil',
    type: 'lei',
    number: '10406',
    year: '2002',
    summary: 'Código Civil Brasileiro, tratando de direitos e obrigações.',
    url: 'https://legislacao.presidencia.gov.br/legislacao/?tipo=LEI&numero=10406&ano=2002',
    tags: ['codigo-civil', 'moderna'],
  },
  {
    title: 'Lei 8.078/1990 - Código de Defesa do Consumidor',
    type: 'lei',
    number: '8078',
    year: '1990',
    summary: 'Proteção dos direitos do consumidor.',
    url: 'https://legislacao.presidencia.gov.br/legislacao/?tipo=LEI&numero=8078&ano=1990',
    tags: ['cdc', 'historica'],
  },
  {
    title: 'Lei 13.709/2018 - LGPD',
    type: 'lei',
    number: '13709',
    year: '2018',
    summary: 'Lei Geral de Proteção de Dados Pessoais.',
    url: 'https://legislacao.presidencia.gov.br/legislacao/?tipo=LEI&numero=13709&ano=2018',
    tags: ['lgpd', 'moderna'],
  },
];

function simulateBrazilianLawSearch(query: string, type: string | undefined, limit: number) {
  const q = query.toLowerCase();
  return SIMULATED_BR_LAWS.filter((law) => (!type || law.type === type) && (law.title.toLowerCase().includes(q) || law.summary.toLowerCase().includes(q))).slice(0, limit);
}

export function createBrazilianLawTools(): MCPTool[] {
  return [
    {
      name: 'search_brazilian_law',
      description: 'Busca leis, jurisprudência ou doutrina brasileiras já ingeridas na base de conhecimento jurídico',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Termo de busca (título, ementa, conteúdo ou tags)' },
          type: {
            type: 'string',
            description: 'Filtra por tipo de documento',
            enum: ['lei', 'jurisprudencia', 'doutrina', 'constituicao'],
          },
          limit: { type: 'number', description: 'Número máximo de resultados', default: 10 },
        },
        required: ['query'],
      },
      execute: async ({ query, type, limit = 10 }) => {
        try {
          const documents = await prisma.legalDocument.findMany({
            where: {
              jurisdiction: 'BR',
              ...(type ? { type } : {}),
              OR: [
                { title: { contains: query, mode: 'insensitive' } },
                { summary: { contains: query, mode: 'insensitive' } },
                { content: { contains: query, mode: 'insensitive' } },
                { tags: { has: query.toLowerCase() } },
              ],
            },
            select: { id: true, title: true, type: true, number: true, year: true, summary: true, url: true, tags: true },
            take: limit,
          });

          if (documents.length === 0) {
            const simulated = simulateBrazilianLawSearch(query, type, limit);
            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(
                    { count: simulated.length, documents: simulated, source: 'simulated', note: 'Nenhum resultado real ingerido ainda; mostrando amostra simulada.' },
                    null,
                    2
                  ),
                },
              ],
              metadata: { count: simulated.length, source: 'simulated' },
            };
          }

          return {
            content: [{ type: 'text', text: JSON.stringify({ count: documents.length, documents, source: 'database' }, null, 2) }],
            metadata: { count: documents.length, source: 'database' },
          };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Erro na busca de legislação BR: ${error.message}` }], isError: true };
        }
      },
    },
    {
      name: 'get_brazilian_law',
      description: 'Obtém o conteúdo completo de uma lei brasileira já ingerida, por ID ou por número/ano',
      inputSchema: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'ID do documento no LegalDocument' },
          number: { type: 'string', description: 'Número da lei (ex.: "10406")' },
          year: { type: 'string', description: 'Ano da lei (ex.: "2002")' },
        },
      },
      execute: async ({ id, number, year }) => {
        try {
          const document = id
            ? await prisma.legalDocument.findUnique({ where: { id } })
            : await prisma.legalDocument.findFirst({
                where: { jurisdiction: 'BR', number, year },
              });

          if (!document) {
            return { content: [{ type: 'text', text: 'Documento não encontrado na base de legislação BR.' }], isError: true };
          }

          return { content: [{ type: 'text', text: JSON.stringify(document, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Erro ao buscar lei BR: ${error.message}` }], isError: true };
        }
      },
    },
  ];
}
