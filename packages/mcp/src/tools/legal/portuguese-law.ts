// packages/mcp/src/tools/legal/portuguese-law.ts
//
// NOTA DE FIDELIDADE: mesmo caso de brazilian-law.ts — o material colado só tinha um
// rascunho comentado (Fase 1.3) para "ingest_legislation_pt", sem corpo real. Reorientado
// para consulta em tempo real da base já ingerida (ver nota completa em
// brazilian-law.ts), espelhando exatamente a mesma estrutura, trocando jurisdiction para 'PT'.
// Fallback simulado (mesma ideia de brazilian-law.ts) acrescentado por simetria — não veio
// do material colado, que só deu o exemplo BR.

import { MCPTool } from '../ToolRegistry';
import { prisma } from './db';

const SIMULATED_PT_LAWS = [
  {
    title: 'Lei 4/2015 - Código Civil',
    type: 'lei',
    number: '4',
    year: '2015',
    summary: 'Código Civil Português, tratando de direitos e obrigações.',
    url: 'https://diariodarepublica.pt/dr/legislacao-consolidada/pesquisa?tipo=lei&numero=4&ano=2015',
    tags: ['codigo-civil', 'moderna'],
  },
  {
    title: 'Lei 58/2019 - RGPD nacional',
    type: 'lei',
    number: '58',
    year: '2019',
    summary: 'Execução do Regulamento Geral de Proteção de Dados em Portugal.',
    url: 'https://diariodarepublica.pt/dr/legislacao-consolidada/pesquisa?tipo=lei&numero=58&ano=2019',
    tags: ['protecao-dados', 'moderna'],
  },
];

function simulatePortugueseLawSearch(query: string, type: string | undefined, limit: number) {
  const q = query.toLowerCase();
  return SIMULATED_PT_LAWS.filter((law) => (!type || law.type === type) && (law.title.toLowerCase().includes(q) || law.summary.toLowerCase().includes(q))).slice(0, limit);
}

export function createPortugueseLawTools(): MCPTool[] {
  return [
    {
      name: 'search_portuguese_law',
      description: 'Busca leis, jurisprudência ou doutrina portuguesas já ingeridas na base de conhecimento jurídico',
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
              jurisdiction: 'PT',
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
            const simulated = simulatePortugueseLawSearch(query, type, limit);
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
          return { content: [{ type: 'text', text: `Erro na busca de legislação PT: ${error.message}` }], isError: true };
        }
      },
    },
    {
      name: 'get_portuguese_law',
      description: 'Obtém o conteúdo completo de uma lei portuguesa já ingerida, por ID ou por número/ano',
      inputSchema: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'ID do documento no LegalDocument' },
          number: { type: 'string', description: 'Número da lei (ex.: "4")' },
          year: { type: 'string', description: 'Ano da lei (ex.: "2015")' },
        },
      },
      execute: async ({ id, number, year }) => {
        try {
          const document = id
            ? await prisma.legalDocument.findUnique({ where: { id } })
            : await prisma.legalDocument.findFirst({
                where: { jurisdiction: 'PT', number, year },
              });

          if (!document) {
            return { content: [{ type: 'text', text: 'Documento não encontrado na base de legislação PT.' }], isError: true };
          }

          return { content: [{ type: 'text', text: JSON.stringify(document, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Erro ao buscar lei PT: ${error.message}` }], isError: true };
        }
      },
    },
  ];
}
