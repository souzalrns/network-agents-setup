// packages/mcp/src/tools/legal/portuguese-law.ts
//
// NOTA DE FIDELIDADE: mesmo caso de brazilian-law.ts — o material colado só tinha um
// rascunho comentado (Fase 1.3) para "ingest_legislation_pt", sem corpo real. Reorientado
// para consulta em tempo real da base já ingerida (ver nota completa em
// brazilian-law.ts), espelhando exatamente a mesma estrutura, trocando jurisdiction para 'PT'.

import { MCPTool } from '../ToolRegistry';
import { prisma } from './db';

export function createPortugueseLawTools(): MCPTool[] {
  return [
    {
      name: 'search_portuguese_law',
      description: 'Busca leis, jurisprudência ou doutrina portuguesas já ingeridas na base de conhecimento jurídico',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Termo de busca (título, ementa ou tags)' },
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
                { tags: { has: query.toLowerCase() } },
              ],
            },
            select: { id: true, title: true, type: true, number: true, year: true, summary: true, url: true, tags: true },
            take: limit,
          });

          return {
            content: [{ type: 'text', text: JSON.stringify({ count: documents.length, documents }, null, 2) }],
            metadata: { count: documents.length },
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
