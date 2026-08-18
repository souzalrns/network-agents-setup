// scripts/ingest/brazilian-law.ts
//
// Colado literalmente pelo usuário, com duas mudanças:
// 1. `const prisma = new PrismaClient()` local foi trocado por
//    `import { prisma } from '../db'` (mesma instância compartilhada por todos os
//    scripts de ingestão, em vez de cada arquivo abrir seu próprio pool de conexão) —
//    consolidação de conveniência, não uma correção de bug.
// 2. A lista original (`getLawList()`) trazia, misturadas com as leis brasileiras, duas
//    leis portuguesas ("Código Civil PT" e "Código de Processo Civil PT") — mas
//    `saveLaw()` grava tudo com `jurisdiction: 'BR'` incondicionalmente, o que salvaria
//    as duas leis PT como se fossem brasileiras. Essas duas entradas foram retiradas
//    daqui e viraram a base do novo `portuguese-law.ts` (autoral, não veio no material
//    colado — a mesma estrutura de código foi replicada para leis PT reais).

import axios from 'axios';
import * as cheerio from 'cheerio';
import { prisma } from '../db';

interface LawData {
  title: string;
  type: string;
  number: string;
  year: string;
  content: string;
  summary: string;
  url: string;
  source: string;
  tags: string[];
  metadata: Record<string, any>;
}

export class BrazilianLawIngestor {
  static async ingestAll(): Promise<{ total: number; inserted: number; updated: number; errors: number }> {
    let inserted = 0;
    let updated = 0;
    let errors = 0;
    let total = 0;

    const laws = this.getLawList();

    for (const law of laws) {
      total++;
      try {
        const data = await this.fetchLaw(law);
        const result = await this.saveLaw(data);
        if (result === 'inserted') inserted++;
        else if (result === 'updated') updated++;
      } catch (error) {
        errors++;
        console.error(`Erro ao ingerir ${law.type} ${law.number}/${law.year}:`, error);
      }
    }

    return { total, inserted, updated, errors };
  }

  private static getLawList(): Array<{ type: string; number: string; year: string }> {
    return [
      // Códigos
      { type: 'lei', number: '10406', year: '2002' }, // Código Civil
      { type: 'lei', number: '13105', year: '2015' }, // Código de Processo Civil
      { type: 'lei', number: '7210', year: '1984' }, // Código de Processo Penal
      { type: 'lei', number: '7209', year: '1984' }, // Código Penal
      { type: 'lei', number: '8112', year: '1990' }, // Servidores Públicos
      { type: 'lei', number: '8666', year: '1993' }, // Licitações
      { type: 'lei', number: '14133', year: '2021' }, // Nova Lei de Licitações
      { type: 'lei', number: '13709', year: '2018' }, // LGPD

      // Leis trabalhistas
      { type: 'lei', number: '5452', year: '1943' }, // CLT
      { type: 'lei', number: '8213', year: '1991' }, // Previdência

      // Leis tributárias
      { type: 'lei', number: '5172', year: '1966' }, // CTN

      // Leis consumeristas
      { type: 'lei', number: '8078', year: '1990' }, // CDC

      // Leis imobiliárias
      { type: 'lei', number: '6015', year: '1973' }, // Registros Públicos
      { type: 'lei', number: '10257', year: '2001' }, // Estatuto da Cidade

      // Leis constitucionais
      { type: 'lei', number: '0001', year: '1988' }, // Constituição Federal
    ];
  }

  private static async fetchLaw(law: { type: string; number: string; year: string }): Promise<LawData> {
    // URL do Planalto
    const url = `https://legislacao.presidencia.gov.br/legislacao/?tipo=${law.type.toUpperCase()}&numero=${law.number}&ano=${law.year}`;

    try {
      const response = await axios.get(url);
      const html = response.data;
      const $ = cheerio.load(html);

      // Extrai dados
      const title = $('h1.titulo').text().trim() || `${law.type.toUpperCase()} ${law.number}/${law.year}`;
      const content = $('div.conteudo').text().trim() || 'Conteúdo não disponível';
      const summary = $('div.ementa').text().trim() || content.slice(0, 200);

      // Tags baseadas no tipo
      const tags = this.getTags(law);

      return {
        title,
        type: law.type,
        number: law.number,
        year: law.year,
        content,
        summary,
        url,
        source: 'planalto',
        tags,
        metadata: {
          fetchedAt: new Date().toISOString(),
          url,
          lawType: law.type,
        },
      };
    } catch (error) {
      // Fallback: dados simulados para teste
      return this.getFallbackLaw(law);
    }
  }

  private static getTags(law: { type: string; number: string; year: string }): string[] {
    const tags: string[] = [];

    // Por tipo
    if (law.type === 'lei') {
      tags.push('lei');
      if (law.number === '10406') tags.push('codigo-civil');
      if (law.number === '13105') tags.push('codigo-processo-civil');
      if (law.number === '5452') tags.push('clt');
      if (law.number === '8078') tags.push('cdc');
      if (law.number === '13709') tags.push('lgpd');
      if (law.number === '8666' || law.number === '14133') tags.push('licitacoes');
    }

    // Por ano
    if (parseInt(law.year) < 2000) tags.push('historica');
    if (parseInt(law.year) >= 2000) tags.push('moderna');

    return tags;
  }

  private static getFallbackLaw(law: { type: string; number: string; year: string }): LawData {
    return {
      title: `${law.type.toUpperCase()} ${law.number}/${law.year}`,
      type: law.type,
      number: law.number,
      year: law.year,
      content: `Conteúdo da ${law.type} ${law.number}/${law.year} (simulado para teste)`,
      summary: `Resumo da ${law.type} ${law.number}/${law.year}`,
      url: `https://legislacao.presidencia.gov.br/legislacao/?tipo=${law.type}&numero=${law.number}&ano=${law.year}`,
      source: 'fallback',
      tags: this.getTags(law),
      metadata: {
        fetchedAt: new Date().toISOString(),
        isFallback: true,
      },
    };
  }

  private static async saveLaw(data: LawData): Promise<'inserted' | 'updated'> {
    const existing = await prisma.legalDocument.findFirst({
      where: {
        source: data.source,
        number: data.number,
        year: data.year,
        type: data.type,
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
        type: data.type,
        jurisdiction: 'BR',
        number: data.number,
        year: data.year,
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
  BrazilianLawIngestor.ingestAll()
    .then((stats) => {
      console.log('📊 Leis brasileiras:', stats);
      process.exit(0);
    })
    .catch((error) => {
      console.error('❌ Erro:', error);
      process.exit(1);
    });
}
