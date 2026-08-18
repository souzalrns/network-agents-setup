// scripts/ingest/doctrine.ts
//
// NOTA DE FIDELIDADE (histórico): não veio no material colado pelo usuário — escrito como
// stub explicitamente simulado ("Conteúdo simulado para teste — substituir por fonte de
// doutrina real"), já que doutrina publicada (livros/artigos) costuma ter direitos autorais
// e exigiria integração com uma base licenciada, que este projeto não tem.
//
// REVISÃO 18/08/2026 — substituído por sínteses doutrinárias ORIGINAIS (texto próprio,
// não cópia de nenhum autor específico) sobre princípios amplamente consolidados e não
// controversos do direito civil BR/PT. Atribuição como "seed" foi trocada por
// "síntese-curada" para não sugerir falsamente que é obra de um autor determinado —
// evita tanto o problema de direitos autorais quanto o de atribuição incorreta.

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
    const entries = this.getCuratedEntries();

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

  private static getCuratedEntries(): DoctrineData[] {
    return [
      {
        title: 'Princípios estruturantes do Código Civil brasileiro de 2002',
        author: 'síntese-curada',
        jurisdiction: 'BR',
        summary: 'Eticidade, socialidade e operabilidade — os três eixos que orientam a interpretação do Código Civil de 2002, em contraste com o individualismo do Código de 1916.',
        content:
          'A doutrina civilista brasileira consolidou três princípios estruturantes do Código Civil de 2002 (Miguel Reale, coordenador da comissão ' +
          'elaboradora, foi quem mais difundiu essa sistematização): (1) Eticidade — valorização da boa-fé objetiva e da equidade sobre o formalismo ' +
          'positivista puro, presente em cláusulas gerais como o art. 187 (abuso de direito) e o art. 422 (boa-fé nos contratos); (2) Socialidade — ' +
          'superação do individualismo do CC/1916 em favor da função social da propriedade (art. 1.228, §1º) e da função social do contrato (art. 421); ' +
          '(3) Operabilidade — busca por soluções simples e efetivas, com uso de cláusulas gerais e conceitos indeterminados que permitem ao julgador ' +
          'adaptar a norma ao caso concreto, em vez de casuísmo excessivo. Esses três eixos são referência comum na doutrina para explicar por que o ' +
          'CC/2002 se afasta do modelo liberal-individualista do código anterior.',
        source: 'sintese-curada',
        tags: ['doutrina', 'brasil', 'civil', 'principios'],
        metadata: { fetchedAt: new Date().toISOString(), isCurated: true },
      },
      {
        title: 'Princípios estruturantes do Código Civil português',
        author: 'síntese-curada',
        jurisdiction: 'PT',
        summary: 'Autonomia privada, boa-fé e abuso de direito como eixos centrais do sistema civilista português, de matriz germânica (BGB) via influência de Manuel de Andrade e Vaz Serra.',
        content:
          'O Código Civil português de 1966 tem forte influência do BGB alemão, sobretudo na sua Parte Geral (matéria incomum nos códigos de matriz ' +
          'francesa). Três princípios centrais orientam a doutrina portuguesa: (1) Autonomia privada — liberdade contratual como regra, com limites ' +
          'nos bons costumes e na ordem pública (art. 280º); (2) Boa-fé — cláusula geral presente na formação e execução dos contratos (art. 227º e ' +
          '762º, n.º 2), usada pela jurisprudência para construir deveres acessórios (informação, lealdade, cooperação) não previstos expressamente no ' +
          'contrato; (3) Abuso de direito (art. 334º) — o titular de um direito que o exerça excedendo manifestamente os limites impostos pela boa-fé, ' +
          'pelos bons costumes ou pelo fim social/econômico do direito, comete um ato ilícito, mesmo agindo dentro dos limites formais do direito. Este ' +
          'último princípio é um dos mais citados na jurisprudência cível portuguesa, incluindo em matéria de relações de vizinhança e arrendamento.',
        source: 'sintese-curada',
        tags: ['doutrina', 'portugal', 'civil', 'principios'],
        metadata: { fetchedAt: new Date().toISOString(), isCurated: true },
      },
      {
        title: 'Função social do contrato: convergência e divergência entre Brasil e Portugal',
        author: 'síntese-curada',
        jurisdiction: 'BR',
        summary: 'O CC brasileiro positiva expressamente a função social do contrato (art. 421); o direito português chega a resultado próximo por via da boa-fé e do abuso de direito, sem cláusula equivalente expressa.',
        content:
          'O art. 421 do Código Civil brasileiro dispõe expressamente que "a liberdade contratual será exercida nos limites da função social do ' +
          'contrato" — uma cláusula geral que permite ao juiz mitigar efeitos contratuais que, embora formalmente válidos, gerem desequilíbrio social ' +
          'incompatível com a boa-fé e a probidade (art. 422). O direito português não tem dispositivo equivalente expresso no Código Civil de 1966 ' +
          '(anterior à Constituição de 1976 e ao próprio conceito difundido de função social do contrato), mas a doutrina e jurisprudência lusas chegam ' +
          'a resultados funcionalmente próximos através da combinação de boa-fé objetiva (art. 762º, n.º 2) e abuso de direito (art. 334º), além de ' +
          'legislação avulsa de proteção do consumidor e do arrendatário. Para um sistema BR-PT (como este PCU se propõe a servir), essa diferença de ' +
          'técnica legislativa — cláusula geral expressa no Brasil vs. construção pretoriana em Portugal — é um ponto de atenção recorrente em pareceres ' +
          'comparativos.',
        source: 'sintese-curada',
        tags: ['doutrina', 'brasil', 'portugal', 'contratos', 'comparado'],
        metadata: { fetchedAt: new Date().toISOString(), isCurated: true },
      },
      {
        title: 'Usucapião: modalidades e requisitos no direito brasileiro',
        author: 'síntese-curada',
        jurisdiction: 'BR',
        summary: 'Panorama das modalidades de usucapião no Brasil (extraordinária, ordinária, especial urbana, especial rural, familiar, extrajudicial) e seus prazos/requisitos.',
        content:
          'Extraordinária (art. 1.238 CC): 15 anos de posse ininterrupta e sem oposição, reduzidos a 10 anos com moradia habitual ou obras produtivas, ' +
          'independentemente de título e boa-fé. Ordinária (art. 1.242 CC): 10 anos com justo título e boa-fé, reduzidos a 5 anos em hipóteses ' +
          'específicas (aquisição onerosa com registro cancelado, moradia ou investimentos de interesse social). Especial urbana (art. 183 CF e art. ' +
          '1.240 CC): 5 anos, área urbana até 250m², moradia própria/familiar, sem outro imóvel. Especial rural (art. 191 CF e art. 1.239 CC): 5 anos, ' +
          'área rural até 50 hectares, produtividade pelo trabalho próprio/familiar. Familiar/por abandono do lar (art. 1.240-A CC, incluído pela Lei ' +
          '12.424/2011): 2 anos, imóvel urbano até 250m² dividido com ex-cônjuge/companheiro que abandonou o lar. Extrajudicial (art. 216-A da Lei ' +
          '6.015/73, incluído pela Lei 11.977/2009): procedimento administrativo em cartório de Registro de Imóveis, aplicável a qualquer modalidade ' +
          'quando há consenso entre os interessados, sem necessidade de ação judicial.',
        source: 'sintese-curada',
        tags: ['doutrina', 'brasil', 'civil', 'usucapiao', 'imobiliario'],
        metadata: { fetchedAt: new Date().toISOString(), isCurated: true },
      },
    ];
  }

  private static async saveDoctrine(data: DoctrineData): Promise<'inserted' | 'updated'> {
    const existing = await prisma.legalDocument.findFirst({
      where: { source: data.source, title: data.title, type: 'doutrina' },
    });

    if (existing) {
      await prisma.legalDocument.update({
        where: { id: existing.id },
        data: { content: data.content, summary: data.summary, metadata: data.metadata, tags: data.tags, updatedAt: new Date() },
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
