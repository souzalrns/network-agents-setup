// scripts/ingest/jurisprudence.ts
//
// Colado literalmente pelo usuário. Única mudança: `const prisma = new PrismaClient()`
// local foi trocado por `import { prisma } from '../db'` (mesma consolidação aplicada
// em brazilian-law.ts). `import axios from 'axios'` do original foi removido porque não
// é usado em nenhum lugar deste arquivo — os métodos STJ/TJSP/tribunais portugueses já
// eram stubs simulados (`return { total: 5, inserted: 5, updated: 0, errors: 0 }`) no
// texto original, e fetchSTFCase() também é simulado, não faz nenhuma chamada HTTP real.

import { prisma } from '../db';

interface JurisprudenceData {
  court: string;
  caseNumber: string;
  date: string;
  summary: string;
  content: string;
  decision: string;
  url: string;
  source: string;
  tags: string[];
  metadata: Record<string, any>;
}

export class JurisprudenceIngestor {
  static async ingestAll(): Promise<{ total: number; inserted: number; updated: number; errors: number }> {
    let inserted = 0;
    let updated = 0;
    let errors = 0;
    let total = 0;

    // STF
    const stf = await this.ingestSTF();
    inserted += stf.inserted;
    updated += stf.updated;
    errors += stf.errors;
    total += stf.total;

    // STJ
    const stj = await this.ingestSTJ();
    inserted += stj.inserted;
    updated += stj.updated;
    errors += stj.errors;
    total += stj.total;

    // TJSP
    const tjsp = await this.ingestTJSP();
    inserted += tjsp.inserted;
    updated += tjsp.updated;
    errors += tjsp.errors;
    total += tjsp.total;

    // Tribunais portugueses
    const pt = await this.ingestPortugueseTribunals();
    inserted += pt.inserted;
    updated += pt.updated;
    errors += pt.errors;
    total += pt.total;

    return { total, inserted, updated, errors };
  }

  private static async ingestSTF(): Promise<{ total: number; inserted: number; updated: number; errors: number }> {
    // Simula ingestão de jurisprudência do STF
    const cases = this.getSTFCases();

    let inserted = 0;
    let updated = 0;
    let errors = 0;
    let total = 0;

    for (const caseData of cases) {
      total++;
      try {
        const data = await this.fetchSTFCase(caseData);
        const result = await this.saveJurisprudence(data);
        if (result === 'inserted') inserted++;
        else if (result === 'updated') updated++;
      } catch (error) {
        errors++;
        console.error(`Erro ao ingerir caso STF ${caseData}:`, error);
      }
    }

    return { total, inserted, updated, errors };
  }

  private static getSTFCases(): string[] {
    return ['RE-123456-7', 'RE-654321-0', 'ADI-4321', 'ADPF-123', 'MS-12345', 'HC-123456'];
  }

  private static async fetchSTFCase(caseNumber: string): Promise<JurisprudenceData> {
    // Simula busca no STF
    return {
      court: 'STF',
      caseNumber,
      date: new Date().toISOString(),
      summary: `Decisão do STF sobre ${caseNumber}`,
      content: `Conteúdo completo da decisão ${caseNumber}`,
      decision: `Decisão final do STF para ${caseNumber}`,
      url: `https://portal.stf.jus.br/processos/${caseNumber}`,
      source: 'stf',
      tags: ['stf', 'jurisprudencia', 'brasil'],
      metadata: {
        fetchedAt: new Date().toISOString(),
        court: 'STF',
      },
    };
  }

  private static async ingestSTJ(): Promise<{ total: number; inserted: number; updated: number; errors: number }> {
    // Similar ao STF
    return { total: 5, inserted: 5, updated: 0, errors: 0 };
  }

  private static async ingestTJSP(): Promise<{ total: number; inserted: number; updated: number; errors: number }> {
    return { total: 5, inserted: 5, updated: 0, errors: 0 };
  }

  private static async ingestPortugueseTribunals(): Promise<{ total: number; inserted: number; updated: number; errors: number }> {
    return { total: 5, inserted: 5, updated: 0, errors: 0 };
  }

  private static async saveJurisprudence(data: JurisprudenceData): Promise<'inserted' | 'updated'> {
    const existing = await prisma.legalDocument.findFirst({
      where: {
        source: data.source,
        number: data.caseNumber,
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
        title: `${data.court} - ${data.caseNumber}`,
        type: 'jurisprudencia',
        jurisdiction: data.court === 'STF' || data.court === 'STJ' ? 'BR' : 'PT',
        number: data.caseNumber,
        year: new Date().getFullYear().toString(),
        summary: data.summary,
        content: data.content,
        url: data.url,
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
  JurisprudenceIngestor.ingestAll()
    .then((stats) => {
      console.log('📊 Jurisprudência:', stats);
      process.exit(0);
    })
    .catch((error) => {
      console.error('❌ Erro:', error);
      process.exit(1);
    });
}
