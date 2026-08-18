// scripts/ingest/portuguese-law.ts
//
// NOTA DE FIDELIDADE (histórico): este arquivo não veio no material colado pelo usuário —
// foi escrito replicando a estrutura de brazilian-law.ts para a fonte oficial portuguesa
// (Diário da República Eletrónico).
//
// REVISÃO 18/08/2026 — a lista original (`getLawList()`) tinha 19 entradas, mas boa parte
// dos números de decreto-lei/lei foi INVENTADA como placeholder (documentado no próprio
// arquivo: "sem pretensão de estar citando o número real do decreto-lei"). Verificar isso
// contra fontes reais (Diário da República, Ordem dos Advogados, pgdlisboa.pt) via busca
// encontrou, entre outras coisas, que:
//
// - O Código Civil português NÃO é "Lei 4/2015" (isso é o Código do Procedimento
//   Administrativo) — o Código Civil é o Decreto-Lei 47.344/66, de 25/11/1966.
// - O Código de Processo Civil NÃO é "Lei 15/2013" — é a Lei 41/2013, de 26/06.
// - Código Penal = Decreto-Lei 400/82, de 23/09 (não estava na lista original).
// - Código de Processo Penal = Decreto-Lei 78/87, de 17/02 (não "Lei 48/2017").
//
// Diante disso, a lista foi REDUZIDA de 19 para 9 entradas: melhor um conjunto menor e
// verificado do que manter números não confirmados apresentados com falsa confiança —
// citação jurídica errada é pior do que ausência de citação (arriscaria o sistema
// "confirmar" uma fonte que não existe). As entradas removidas (Código do IVA, IRS, IRC,
// Lei das Garantias, Regime do Arrendamento/Condomínio, Lei do Contrato de Trabalho em
// Funções Públicas etc.) ficam pendentes de verificação antes de reentrar na lista.

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

interface LawRef {
  type: string;
  number: string;
  year: string;
  titleOverride?: string;
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

  // Lista verificada (ver nota de fidelidade no topo do arquivo). Cada entrada foi
  // confirmada por busca contra fonte oficial/confiável antes de entrar aqui.
  private static getLawList(): LawRef[] {
    return [
      { type: 'decreto-lei', number: '47344', year: '1966', titleOverride: 'Código Civil' },
      { type: 'lei', number: '41', year: '2013', titleOverride: 'Código de Processo Civil' },
      { type: 'decreto-lei', number: '78', year: '1987', titleOverride: 'Código de Processo Penal' },
      { type: 'decreto-lei', number: '400', year: '1982', titleOverride: 'Código Penal' },
      { type: 'lei', number: '7', year: '2009' }, // Código do Trabalho
      { type: 'lei', number: '58', year: '2019' }, // Lei de execução nacional do RGPD
      { type: 'lei', number: '24', year: '1996' }, // Lei de Defesa do Consumidor
      { type: 'decreto-lei', number: '4', year: '2015', titleOverride: 'Código do Procedimento Administrativo' },
      { type: 'constituicao', number: '0', year: '1976', titleOverride: 'Constituição da República Portuguesa' },
    ];
  }

  private static async fetchLaw(law: LawRef): Promise<LawData> {
    // URL do Diário da República Eletrónico (fonte oficial da legislação portuguesa)
    const url = `https://diariodarepublica.pt/dr/legislacao-consolidada/pesquisa?tipo=${law.type}&numero=${law.number}&ano=${law.year}`;

    try {
      const response = await axios.get(url);
      const html = response.data;
      const $ = cheerio.load(html);

      const title = $('h1.titulo').text().trim() || law.titleOverride || `${law.type} n.º ${law.number}/${law.year}`;
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
        metadata: { fetchedAt: new Date().toISOString(), url, lawType: law.type },
      };
    } catch (error) {
      // DRE está bloqueado neste sandbox — usa o conteúdo curado real (ver nota de
      // fidelidade no topo do arquivo).
      return this.getSeedContent(law);
    }
  }

  private static getTags(law: LawRef): string[] {
    const tags: string[] = ['portugal'];

    if (law.type === 'lei' || law.type === 'decreto-lei') tags.push('lei');
    if (law.type === 'constituicao') tags.push('constituicao');
    if (law.number === '47344') tags.push('codigo-civil');
    if (law.number === '41' && law.year === '2013') tags.push('codigo-processo-civil');
    if (law.number === '78' && law.year === '1987') tags.push('codigo-processo-penal');
    if (law.number === '400' && law.year === '1982') tags.push('codigo-penal');
    if (law.number === '7' && law.year === '2009') tags.push('codigo-trabalho');
    if (law.number === '58' && law.year === '2019') tags.push('protecao-dados');
    if (law.number === '4' && law.year === '2015') tags.push('procedimento-administrativo');

    if (parseInt(law.year) < 2000) tags.push('historica');
    if (parseInt(law.year) >= 2000) tags.push('moderna');

    return tags;
  }

  private static getSeedContent(law: LawRef): LawData {
    const seed = PT_LAW_CONTENT[`${law.number}/${law.year}`];
    const title = law.titleOverride || seed?.title || `${law.type} n.º ${law.number}/${law.year}`;
    const summary = seed?.summary || `Resumo indisponível para ${title}.`;
    const content = seed?.content || `Resumo indisponível para ${title} — verbete pendente de curadoria.`;

    return {
      title,
      type: law.type,
      number: law.number,
      year: law.year,
      content,
      summary,
      url: `https://diariodarepublica.pt/dr/legislacao-consolidada/pesquisa?tipo=${law.type}&numero=${law.number}&ano=${law.year}`,
      source: 'seed-curado',
      tags: this.getTags(law),
      metadata: { fetchedAt: new Date().toISOString(), isCurated: true },
    };
  }

  private static async saveLaw(data: LawData): Promise<'inserted' | 'updated'> {
    const existing = await prisma.legalDocument.findFirst({
      where: { source: data.source, number: data.number, year: data.year, type: data.type },
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

const PT_LAW_CONTENT: Record<string, { title: string; summary: string; content: string }> = {
  '47344/1966': {
    title: 'Código Civil',
    summary: 'Decreto-Lei 47.344/66 — disciplina relações entre particulares em Portugal: pessoas, negócio jurídico, direito das obrigações, coisas, família e sucessões.',
    content:
      'Livro I — Parte Geral: pessoas singulares e coletivas, negócio jurídico, prescrição e caducidade (arts. 66-333). Livro II — Direito das Obrigações: ' +
      'fontes das obrigações (contratos, responsabilidade civil), cumprimento e incumprimento, garantias (arts. 397-1250). Livro III — Direito das ' +
      'Coisas: posse, propriedade, usucapião (arts. 1287-1315 e 1316-1446), direitos reais menores. Livro IV — Direito da Família: casamento, regimes de ' +
      'bens (comunhão geral, comunhão de adquiridos, separação — arts. 1698-1734), divórcio, filiação (arts. 1576-2020). Livro V — Direito das Sucessões: ' +
      'sucessão legítima, legitimária e testamentária (arts. 2024-2334). Uma das codificações civis mais influentes dos países lusófonos, com múltiplas ' +
      'revisões (a mais estrutural em 1977, pós-Constituição de 1976).',
  },
  '41/2013': {
    title: 'Código de Processo Civil',
    summary: 'Lei 41/2013, de 26/06 — regula o processo civil português, com simplificação processual e reforço da gestão processual pelo juiz.',
    content:
      'Princípios fundamentais: dever de gestão processual, adequação formal, cooperação e boa-fé processual (arts. 6º-8º). Processo declarativo comum ' +
      'sem distinção de formas (sumária/ordinária) — unificado num único procedimento comum (arts. 548 e seguintes). Articulados: petição inicial, ' +
      'contestação, audiência prévia (arts. 552-593). Instrução e julgamento, sentença (arts. 594-620). Recursos: apelação, revista (arts. 627-697). ' +
      'Processo executivo: penhora, venda de bens (arts. 707-877). Substituiu o CPC de 1961 (que já tinha sofrido revisão profunda em 1995-96).',
  },
  '78/1987': {
    title: 'Código de Processo Penal',
    summary: 'Decreto-Lei 78/87, de 17/02 — disciplina o processo penal português: inquérito, instrução, julgamento e recursos.',
    content:
      'Fase de inquérito dirigida pelo Ministério Público, com apoio de órgãos de polícia criminal (arts. 262-286). Fase de instrução facultativa, a ' +
      'requerimento do arguido ou assistente (arts. 286-310). Julgamento perante tribunal singular ou coletivo, conforme a moldura penal (arts. 311-379). ' +
      'Medidas de coação: termo de identidade e residência, obrigação de apresentação periódica, prisão preventiva como último recurso (arts. 191-224). ' +
      'Recursos ordinários e extraordinários (arts. 399-467). Estrutura acusatória com contraditório desde a fase de inquérito nos atos que o exijam.',
  },
  '400/1982': {
    title: 'Código Penal',
    summary: 'Decreto-Lei 400/82, de 23/09, revisto e republicado pelo Decreto-Lei 48/95 — define crimes e penas em Portugal.',
    content:
      'Parte Geral: princípio da legalidade, aplicação da lei penal no tempo e no espaço, teoria do crime, formas de crime (tentativa, comparticipação), ' +
      'penas e medidas de segurança, suspensão da execução da pena (arts. 1º-130). Parte Especial: crimes contra as pessoas (homicídio art. 131, ofensa à ' +
      'integridade física art. 143), crimes contra o património (furto art. 203, roubo art. 210, burla art. 217), crimes contra a vida em sociedade, ' +
      'crimes contra o Estado (arts. 131-386). Substituiu o Código Penal de 1886 (de matriz oitocentista). Revisto dezenas de vezes desde 1995.',
  },
  '7/2009': {
    title: 'Código do Trabalho',
    summary: 'Lei 7/2009, de 12/02 — regula as relações de trabalho subordinado em Portugal: contrato, retribuição, tempo de trabalho e cessação.',
    content:
      'Contrato de trabalho: período experimental, contrato a termo (certo/incerto), trabalho temporário (arts. 111-192). Tempo de trabalho: período ' +
      'normal de trabalho (8h/dia, 40h/semana), trabalho suplementar, descanso semanal, férias — mínimo 22 dias úteis (arts. 197-254). Retribuição: ' +
      'salário mínimo nacional, subsídio de férias e de Natal (arts. 258-282). Cessação do contrato: despedimento por justa causa, despedimento coletivo, ' +
      'extinção do posto de trabalho, caducidade, revogação por acordo (arts. 338-393). Segurança e saúde no trabalho (arts. 281-284, remetendo para ' +
      'legislação específica). Substituiu o Código do Trabalho de 2003, com revisão profunda pela Lei 23/2012 e alterações posteriores.',
  },
  '58/2019': {
    title: 'Lei de execução do RGPD em Portugal',
    summary: 'Lei 58/2019, de 08/08 — assegura a aplicação do Regulamento Geral de Proteção de Dados (RGPD/UE 2016/679) na ordem jurídica portuguesa.',
    content:
      'Complementa o RGPD com regras nacionais: idade de consentimento para serviços da sociedade da informação fixada em 13 anos (art. 16º); regime ' +
      'sancionatório nacional com contraordenações e coimas que podem chegar aos tetos do RGPD (4% do volume de negócios ou 20 milhões de euros — arts. ' +
      '37-46); competências da CNPD (Comissão Nacional de Proteção de Dados) como autoridade de controlo (arts. 3º-6º); regras específicas para ' +
      'tratamento de dados no contexto laboral e de videovigilância. Complementar ao Regulamento europeu, que é diretamente aplicável desde 25/05/2018.',
  },
  '24/1996': {
    title: 'Lei de Defesa do Consumidor',
    summary: 'Lei 24/96, de 31/07 — estabelece o regime legal de proteção do consumidor em Portugal.',
    content:
      'Direitos do consumidor: qualidade dos bens e serviços, proteção da saúde e segurança, formação e informação, proteção dos interesses econômicos, ' +
      'prevenção de práticas lesivas, reparação de danos (art. 3º). Direito à informação em particular: rotulagem, publicidade, preços (arts. 7º-9º). ' +
      'Cláusulas contratuais gerais e contratos de adesão remetem para o DL 446/85. Garantia legal de conformidade de bens de consumo regulada em diploma ' +
      'próprio (DL 84/2021, que transpôs a Diretiva (UE) 2019/771). Direito de queixa e acesso a mecanismos de resolução alternativa de litígios de ' +
      'consumo (art. 14º).',
  },
  '4/2015': {
    title: 'Código do Procedimento Administrativo',
    summary: 'Decreto-Lei 4/2015, de 07/01 — regula o procedimento administrativo em Portugal: princípios da atividade administrativa, ato e procedimento administrativo.',
    content:
      'Princípios gerais da atividade administrativa: legalidade, prossecução do interesse público, proporcionalidade, boa administração, proteção da ' +
      'confiança, boa-fé (arts. 3º-19). Procedimento administrativo: início, instrução, audiência dos interessados, decisão (arts. 53-129). Ato ' +
      'administrativo: elementos, validade, invalidade (nulidade e anulabilidade), revogação (arts. 148-175). Contrato administrativo: regras gerais ' +
      '(arts. 200-203, remetendo em grande parte para o Código dos Contratos Públicos). Substituiu o CPA de 1991, com reforma que incorporou jurisprudência ' +
      'consolidada e o Código de Processo nos Tribunais Administrativos.',
  },
  '0/1976': {
    title: 'Constituição da República Portuguesa',
    summary: 'Lei fundamental do Estado português, aprovada após a Revolução de 25 de abril de 1974 — direitos fundamentais, organização do poder político.',
    content:
      'Parte I — Direitos e Deveres Fundamentais (arts. 12-79): direitos, liberdades e garantias pessoais (arts. 24-47), direitos económicos, sociais e ' +
      'culturais (arts. 58-79). Parte II — Organização Econômica (arts. 80-107). Parte III — Organização do Poder Político (arts. 108-276): Presidente ' +
      'da República, Assembleia da República, Governo, Tribunais (incluindo Tribunal Constitucional), poder local. Parte IV — Garantia e Revisão da ' +
      'Constituição (arts. 277-296): fiscalização da constitucionalidade, processo de revisão constitucional (exige maioria de dois terços). Já sofreu ' +
      'sete revisões constitucionais desde 1976 (a mais recente em 2005). Regime da nacionalidade regulado por lei ordinária (Lei 37/81), não pela ' +
      'Constituição diretamente.',
  },
};

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
