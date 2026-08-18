// scripts/ingest/doctrine.ts
//
// NOTA DE FIDELIDADE: este arquivo NÃO veio no material colado pelo usuário — a "Fase 3"
// do plano menciona ingestão de doutrina e scripts/ingest/index.ts importa e chama
// `DoctrineIngestor.ingestAll()`, mas nenhum código foi colado para esta classe. Foi
// escrito como um stub simulado, no mesmo espírito dos métodos ingestSTJ/ingestTJSP/
// ingestPortugueseTribunals de jurisprudence.ts (que no material original também são só
// `return { total: 5, inserted: 5, updated: 0, errors: 0 }`, sem chamada externa real) —
// aqui documentado explicitamente como não-implementado, para não passar a falsa
// impressão de que já busca doutrina de verdade.

import { prisma } from '../db';

interface DoctrineData {
  title: string;
  author: string;
  jurisdiction: 'BR' | 'PT';
  summary: string;
  content: string;
  source: string;
  tags: string[];
  metadata: Record<string, any>;
}

export class DoctrineIngestor {
  static async ingestAll(): Promise<{ total: number; inserted: number; updated: number; errors: number }> {
    // Ainda não há fonte de doutrina configurada (livros/artigos jurídicos costumam ter
    // direitos autorais e exigir integração com uma base licenciada). Por enquanto,
    // ingere um pequeno conjunto de verbetes simulados só para a capability não ficar
    // vazia — igual ao padrão dos stubs de jurisprudence.ts.
    const entries = this.getSeedEntries();

    let inserted = 0;
    let updated = 0;
    let errors = 0;
    let total = 0;

    for (const entry of entries) {
      total++;
      try {
        const result = await this.saveDoctrine(entry);
        if (result === 'inserted') inserted++;
        else if (result === 'updated') updated++;
      } catch (error) {
        errors++;
        console.error(`Erro ao ingerir doutrina "${entry.title}":`, error);
      }
    }

    return { total, inserted, updated, errors };
  }

  private static getSeedEntries(): DoctrineData[] {
    return [
      {
        title: 'Princípios do Direito Civil Brasileiro',
        author: 'seed',
        jurisdiction: 'BR',
        summary: 'Resumo introdutório sobre os princípios que orientam o Código Civil (simulado).',
        content: 'Conteúdo simulado para teste — substituir por fonte de doutrina real.',
        source: 'fallback',
        tags: ['doutrina', 'brasil', 'civil'],
        metadata: { fetchedAt: new Date().toISOString(), isFallback: true },
      },
      {
        title: 'Princípios do Direito Civil Português',
        author: 'seed',
        jurisdiction: 'PT',
        summary: 'Resumo introdutório sobre os princípios que orientam o Código Civil português (simulado).',
        content: 'Conteúdo simulado para teste — substituir por fonte de doutrina real.',
        source: 'fallback',
        tags: ['doutrina', 'portugal', 'civil'],
        metadata: { fetchedAt: new Date().toISOString(), isFallback: true },
      },
    ];
  }

  private static async saveDoctrine(data: DoctrineData): Promise<'inserted' | 'updated'> {
    const existing = await prisma.legalDocument.findFirst({
      where: {
        source: data.source,
        title: data.title,
        type: 'doutrina',
      },
    });

    if (existing) {
      await prisma.legalDocument.update({
        where: { id: existing.id },
        data: {
          content: data.content,
          summary: data.summary,
          metadata: data.metadata,
          tags: data.tags,
          updatedAt: new Date(),
        },
      });
      return 'updated';
    }

    await prisma.legalDocument.create({
      data: {
        title: data.title,
        type: 'doutrina',
        jurisdiction: data.jurisdiction,
        summary: data.summary,
        content: data.content,
        source: data.source,
        tags: data.tags,
        metadata: data.metadata,
      },
    });
    return 'inserted';
  }
}

// Executa se for chamado diretamente
if (require.main === module) {
  DoctrineIngestor.ingestAll()
    .then((stats) => {
      console.log('📊 Doutrina:', stats);
      process.exit(0);
    })
    .catch((error) => {
      console.error('❌ Erro:', error);
      process.exit(1);
    });
}
