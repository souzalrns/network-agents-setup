// scripts/ingest/portuguese-law.ts
//
// NOTA DE FIDELIDADE: este arquivo NÃO veio no material colado pelo usuário — só o nome
// e a responsabilidade ("scripts/ingest/portuguese-law.ts", importado por
// scripts/ingest/index.ts) foram especificados, sem código. Foi escrito replicando a
// estrutura exata de brazilian-law.ts (mesmos nomes de método, mesmo fallback simulado,
// mesmo formato de retorno), trocando a fonte para o Diário da República Eletrónico
// (fonte oficial de legislação portuguesa) e `jurisdiction: 'PT'`. As duas leis
// portuguesas que estavam misturadas na lista original de brazilian-law.ts (Código Civil
// e Código de Processo Civil de Portugal) foram incorporadas aqui.
//
// `getLawList()` foi expandida com a lista maior que o usuário mandou depois, com um
// ajuste: o texto colado tinha `{ type: 'lei', number: '4', year: '2015' }` DUAS vezes
// (uma para "Código Civil", outra para "Código do Procedimento Administrativo") — como
// `saveLaw()` identifica um documento existente por `{source, number, year, type}`, as
// duas entradas colidiam na mesma chave e a segunda ingestão sobrescreveria o conteúdo
// da primeira sob o título errado (mantendo o título de "Código Civil" no `create()`
// inicial, já que `update()` não reescreve `title`). Renumerada para não colidir; sem
// pretensão de estar citando o número real do decreto-lei (a lista inteira já é um seed
// simulado, não uma fonte jurídica verificada).

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

export class PortugueseLawIngestor {
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
      { type: 'lei', number: '4', year: '2015' }, // Código Civil (Decreto-Lei relevante)
      { type: 'lei', number: '15', year: '2013' }, // Código de Processo Civil
      { type: 'lei', number: '7', year: '2009' }, // Código do Trabalho
      { type: 'lei', number: '58', year: '2019' }, // RGPD nacional
      { type: 'lei', number: '24', year: '1996' }, // Lei de Defesa do Consumidor
      { type: 'constituicao', number: '0', year: '1976' }, // Constituição da República Portuguesa
      { type: 'lei', number: '48', year: '2017' }, // Código de Processo Penal
      { type: 'lei', number: '7', year: '2010' }, // Código Penal
      { type: 'lei', number: '23', year: '2012' }, // Lei do Trabalho (revisão)
      { type: 'lei', number: '2', year: '2014' }, // Código do IVA
      { type: 'lei', number: '6', year: '2015' }, // Código do IRS
      { type: 'lei', number: '1', year: '2013' }, // Código do IRC
      { type: 'lei', number: '24', year: '2014' }, // Lei do Consumidor
      { type: 'lei', number: '15', year: '2015' }, // Lei das Garantias
      { type: 'lei', number: '48', year: '2015' }, // Regime do Arrendamento
      { type: 'lei', number: '80', year: '2015' }, // Regime do Condomínio
      { type: 'lei', number: '59', year: '2019' }, // Lei de Proteção de Dados PT
      { type: 'lei', number: '36', year: '2015' }, // Código do Procedimento Administrativo (renumerado — ver nota de fidelidade)
      { type: 'lei', number: '3', year: '2017' }, // Lei do Contrato de Trabalho em Funções Públicas
    ];
  }

  private static async fetchLaw(law: { type: string; number: string; year: string }): Promise<LawData> {
    // URL do Diário da República Eletrónico (fonte oficial da legislação portuguesa)
    const url = `https://diariodarepublica.pt/dr/legislacao-consolidada/pesquisa?tipo=${law.type}&numero=${law.number}&ano=${law.year}`;

    try {
      const response = await axios.get(url);
      const html = response.data;
      const $ = cheerio.load(html);

      const title = $('h1.titulo').text().trim() || `${law.type} n.º ${law.number}/${law.year}`;
      const content = $('div.conteudo').text().trim() || 'Conteúdo não disponível';
      const summary = $('div.ementa').text().trim() || content.slice(0, 200);

      const tags = this.getTags(law);

      return {
        title,
        type: law.type,
        number: law.number,
        year: law.year,
        content,
        summary,
        url,
        source: 'diario-da-republica',
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
    const tags: string[] = ['portugal'];

    if (law.type === 'lei') tags.push('lei');
    if (law.type === 'constituicao') tags.push('constituicao');
    if (law.number === '4' && law.year === '2015') tags.push('codigo-civil');
    if (law.number === '15' && law.year === '2013') tags.push('codigo-processo-civil');
    if (law.number === '7' && law.year === '2009') tags.push('codigo-trabalho');
    if (law.number === '58' && law.year === '2019') tags.push('protecao-dados');
    if (law.number === '48' && law.year === '2017') tags.push('codigo-processo-penal');
    if (law.number === '7' && law.year === '2010') tags.push('codigo-penal');
    if (law.number === '59' && law.year === '2019') tags.push('protecao-dados');

    if (parseInt(law.year) < 2000) tags.push('historica');
    if (parseInt(law.year) >= 2000) tags.push('moderna');

    return tags;
  }

  private static getFallbackLaw(law: { type: string; number: string; year: string }): LawData {
    return {
      title: `${law.type} n.º ${law.number}/${law.year}`,
      type: law.type,
      number: law.number,
      year: law.year,
      content: `Conteúdo da ${law.type} n.º ${law.number}/${law.year} (simulado para teste)`,
      summary: `Resumo da ${law.type} n.º ${law.number}/${law.year}`,
      url: `https://diariodarepublica.pt/dr/legislacao-consolidada/pesquisa?tipo=${law.type}&numero=${law.number}&ano=${law.year}`,
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
        jurisdiction: 'PT',
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
  PortugueseLawIngestor.ingestAll()
    .then((stats) => {
      console.log('📊 Leis portuguesas:', stats);
      process.exit(0);
    })
    .catch((error) => {
      console.error('❌ Erro:', error);
      process.exit(1);
    });
}
