// scripts/ingest/brazilian-law.ts
//
// NOTA DE FIDELIDADE (histórico): o texto original colado pelo usuário fazia
// `const prisma = new PrismaClient()` local — trocado por `import { prisma } from '../db'`
// (mesma instância compartilhada por todos os scripts de ingestão). A lista original
// também trazia, misturadas com as leis brasileiras, duas leis portuguesas — removidas
// daqui e viraram a base de `portuguese-law.ts`.
//
// REVISÃO 18/08/2026 — conteúdo real substituindo placeholder ("Conteúdo simulado para
// teste"), a pedido explícito do usuário para este repo servir como demo/portfólio
// crível da camada genérica do PCU (ver docs/STATUS.md). Duas correções de citação
// encontradas ao escrever o conteúdo real (a lista original tinha os números certos só
// por coincidência de formato, mas apontando para o diploma errado):
//
// 1. `{ number: '7210', year: '1984' }` estava rotulada "Código de Processo Penal" — mas
//    a Lei 7.210/1984 é a Lei de Execução Penal (LEP), não o CPP. O CPP brasileiro é o
//    Decreto-Lei 3.689/1941. Trocado.
// 2. `{ number: '7209', year: '1984' }` estava rotulada "Código Penal" — mas a Lei
//    7.209/1984 é a lei que REFORMOU a Parte Geral do Código Penal, não o Código Penal em
//    si. O Código Penal brasileiro é o Decreto-Lei 2.848/1940. Trocado.
//
// Como o scraping do Planalto está bloqueado neste sandbox (egress falha sempre, ver
// docs/STATUS.md), o "fallback" deixou de ser uma exceção rara — é o caminho normal aqui.
// Por isso ele virou a fonte de conteúdo real e curada (getSeedContent()), não mais um
// texto genérico de "simulado para teste".

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

  private static getLawList(): LawRef[] {
    return [
      // Códigos
      { type: 'lei', number: '10406', year: '2002' }, // Código Civil
      { type: 'lei', number: '13105', year: '2015' }, // Código de Processo Civil
      { type: 'decreto-lei', number: '3689', year: '1941', titleOverride: 'Código de Processo Penal' },
      { type: 'decreto-lei', number: '2848', year: '1940', titleOverride: 'Código Penal' },
      { type: 'lei', number: '8112', year: '1990' }, // Servidores Públicos
      { type: 'lei', number: '8666', year: '1993' }, // Licitações (antiga, ainda referenciada)
      { type: 'lei', number: '14133', year: '2021' }, // Nova Lei de Licitações
      { type: 'lei', number: '13709', year: '2018' }, // LGPD

      // Leis trabalhistas
      { type: 'decreto-lei', number: '5452', year: '1943', titleOverride: 'Consolidação das Leis do Trabalho (CLT)' },
      { type: 'lei', number: '8213', year: '1991' }, // Previdência

      // Leis tributárias
      { type: 'lei', number: '5172', year: '1966' }, // CTN

      // Leis consumeristas
      { type: 'lei', number: '8078', year: '1990' }, // CDC

      // Leis imobiliárias
      { type: 'lei', number: '6015', year: '1973' }, // Registros Públicos
      { type: 'lei', number: '10257', year: '2001' }, // Estatuto da Cidade

      // Constituição
      { type: 'constituicao', number: '0', year: '1988', titleOverride: 'Constituição da República Federativa do Brasil' },
    ];
  }

  private static async fetchLaw(law: LawRef): Promise<LawData> {
    // URL do Planalto
    const url = `https://legislacao.presidencia.gov.br/legislacao/?tipo=${law.type.toUpperCase()}&numero=${law.number}&ano=${law.year}`;

    try {
      const response = await axios.get(url);
      const html = response.data;
      const $ = cheerio.load(html);

      const title = $('h1.titulo').text().trim() || law.titleOverride || `${law.type.toUpperCase()} ${law.number}/${law.year}`;
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
        source: 'planalto',
        tags,
        metadata: { fetchedAt: new Date().toISOString(), url, lawType: law.type },
      };
    } catch (error) {
      // Planalto está bloqueado neste sandbox — usa o conteúdo curado real (ver nota de
      // fidelidade no topo do arquivo).
      return this.getSeedContent(law);
    }
  }

  private static getTags(law: LawRef): string[] {
    const tags: string[] = [];

    if (law.type === 'lei' || law.type === 'decreto-lei') {
      tags.push('lei');
      if (law.number === '10406') tags.push('codigo-civil');
      if (law.number === '13105') tags.push('codigo-processo-civil');
      if (law.number === '3689') tags.push('codigo-processo-penal');
      if (law.number === '2848') tags.push('codigo-penal');
      if (law.number === '5452') tags.push('clt');
      if (law.number === '8078') tags.push('cdc');
      if (law.number === '13709') tags.push('lgpd');
      if (law.number === '8666' || law.number === '14133') tags.push('licitacoes');
    }
    if (law.type === 'constituicao') tags.push('constituicao');

    if (parseInt(law.year) < 2000) tags.push('historica');
    if (parseInt(law.year) >= 2000) tags.push('moderna');

    return tags;
  }

  // Conteúdo real e curado, escrito a partir de conhecimento jurídico geral (não é cópia
  // literal do texto oficial — é um resumo substantivo dos pontos centrais de cada
  // diploma, com os artigos mais citados). Usado sempre neste sandbox, já que o acesso
  // real ao Planalto está bloqueado (ver docs/STATUS.md).
  private static getSeedContent(law: LawRef): LawData {
    const seed = BR_LAW_CONTENT[`${law.number}/${law.year}`];
    const title = law.titleOverride || seed?.title || `Lei ${law.number}/${law.year}`;
    const summary = seed?.summary || `Resumo indisponível para ${title}.`;
    const content = seed?.content || `Resumo indisponível para ${title} — verbete pendente de curadoria.`;

    return {
      title,
      type: law.type,
      number: law.number,
      year: law.year,
      content,
      summary,
      url: `https://legislacao.presidencia.gov.br/legislacao/?tipo=${law.type}&numero=${law.number}&ano=${law.year}`,
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

const BR_LAW_CONTENT: Record<string, { title: string; summary: string; content: string }> = {
  '10406/2002': {
    title: 'Código Civil',
    summary: 'Disciplina as relações entre particulares: pessoas, bens, fatos jurídicos, obrigações, contratos, responsabilidade civil, direito de empresa, coisas, família e sucessões.',
    content:
      'Estruturado em Parte Geral (Livros I-III: pessoas, bens, fatos jurídicos) e Parte Especial (Livros I-V: obrigações, empresa, coisas, família, sucessões). ' +
      'Pontos centrais: capacidade civil e personalidade (arts. 1º-10); direitos da personalidade (arts. 11-21); classificação dos bens (arts. 79-103); ' +
      'negócio jurídico e seus defeitos (arts. 138-184); prescrição e decadência (arts. 189-211); teoria geral das obrigações e contratos (arts. 233-853); ' +
      'responsabilidade civil, subjetiva e objetiva (arts. 186, 187 e 927-954); direito de família — casamento, união estável, regimes de bens, poder familiar ' +
      '(arts. 1.511-1.783); direito das sucessões — sucessão legítima e testamentária, herdeiros necessários (arts. 1.784-2.027). Revogou o Código Civil de 1916.',
  },
  '13105/2015': {
    title: 'Código de Processo Civil',
    summary: 'Regula o processo civil brasileiro: normas fundamentais, competência, atos processuais, tutela provisória, procedimento comum e recursos.',
    content:
      'Substituiu o CPC/1973 com foco em cooperação processual, precedentes e eficiência. Normas fundamentais do processo civil (arts. 1º-12), incluindo ' +
      'contraditório efetivo e vedação à decisão-surpresa. Tutela provisória (urgência e evidência, arts. 294-311). Procedimento comum: petição inicial, ' +
      'contestação, audiência de conciliação/mediação obrigatória (art. 334), saneamento, instrução, sentença (arts. 319-512). Sistema de precedentes ' +
      'vinculantes — IRDR, recursos repetitivos, súmulas vinculantes (arts. 926-928). Recursos: apelação, agravo de instrumento, recurso especial e ' +
      'extraordinário (arts. 994-1.044). Cumprimento de sentença e execução (arts. 513-925).',
  },
  '3689/1941': {
    title: 'Código de Processo Penal',
    summary: 'Decreto-Lei 3.689/1941 — disciplina o processo penal brasileiro: inquérito policial, ação penal, provas, prisões cautelares e recursos.',
    content:
      'Inquérito policial (arts. 4º-23) como procedimento investigatório preliminar. Ação penal pública e privada (arts. 24-62). Prova: exame de corpo de ' +
      'delito, testemunhas, reconhecimento, busca e apreensão, interrogatório (arts. 158-250). Prisão em flagrante, preventiva e temporária (Lei 7.960/89), ' +
      'medidas cautelares diversas da prisão (art. 319, incluído pela Lei 12.403/2011). Procedimentos: comum ordinário/sumário e especiais (júri, arts. ' +
      '406-497). Recursos: apelação, recurso em sentido estrito, embargos, habeas corpus (arts. 574-667). Amplamente alterado por leis posteriores ' +
      '(reforma do júri em 2008, pacote anticrime — Lei 13.964/2019).',
  },
  '2848/1940': {
    title: 'Código Penal',
    summary: 'Decreto-Lei 2.848/1940 — define crimes e penas no Brasil, dividido em Parte Geral (princípios, pena, punibilidade) e Parte Especial (tipos penais).',
    content:
      'Parte Geral (arts. 1º-120, com nova redação pela Lei 7.209/1984): princípio da legalidade, aplicação da lei penal, teoria do crime (fato típico, ' +
      'ilicitude, culpabilidade), concurso de pessoas e crimes, penas (privativas de liberdade, restritivas de direitos, multa), regimes de cumprimento, ' +
      'extinção da punibilidade (prescrição, decadência). Parte Especial (arts. 121-361): crimes contra a pessoa (homicídio art. 121, lesão corporal art. ' +
      '129), contra o patrimônio (furto art. 155, roubo art. 157, estelionato art. 171), contra a dignidade sexual, contra a fé pública, contra a ' +
      'administração pública (peculato art. 312, corrupção art. 317/333). Amplamente complementado por leis penais especiais (drogas, armas, crimes ' +
      'ambientais, LGPD etc.).',
  },
  '8112/1990': {
    title: 'Regime Jurídico dos Servidores Públicos Civis da União',
    summary: 'Estatuto dos servidores públicos federais: provimento, vacância, direitos, deveres, regime disciplinar e processo administrativo.',
    content:
      'Provimento (nomeação, posse, exercício — arts. 5º-15), vacância (exoneração, demissão, aposentadoria — arts. 33-34). Direitos e vantagens: ' +
      'vencimento, indenizações, gratificações, férias, licenças (arts. 40-102). Regime disciplinar: deveres, proibições, penalidades (advertência, ' +
      'suspensão, demissão — arts. 116-142). Processo administrativo disciplinar (PAD) e sindicância (arts. 143-182). Regime previdenciário próprio.',
  },
  '8666/1993': {
    title: 'Lei de Licitações e Contratos Administrativos (antiga)',
    summary: 'Normas gerais de licitação e contratos da Administração Pública — progressivamente substituída pela Lei 14.133/2021, mas ainda referenciada em contratos vigentes.',
    content:
      'Modalidades: concorrência, tomada de preços, convite, concurso, leilão (art. 22). Tipos de licitação: menor preço, melhor técnica, técnica e preço ' +
      '(art. 45). Dispensa e inexigibilidade de licitação (arts. 24-25). Contratos administrativos: cláusulas exorbitantes, garantias, alterações ' +
      'unilaterais (arts. 54-80). Sanções administrativas (arts. 86-88). Revogada progressivamente pela Lei 14.133/2021, com período de transição em que ' +
      'a Administração pode optar por qualquer dos dois regimes.',
  },
  '14133/2021': {
    title: 'Nova Lei de Licitações e Contratos Administrativos',
    summary: 'Substitui a Lei 8.666/1993, a Lei do Pregão e o RDC — moderniza licitações com foco em governança, integridade e julgamento por maior desconto/melhor técnica.',
    content:
      'Unifica em um só diploma o regime da Lei 8.666/93, Lei 10.520/2002 (Pregão) e Lei 12.462/2011 (RDC). Modalidades: pregão, concorrência, concurso, ' +
      'leilão, diálogo competitivo (art. 28). Critérios de julgamento: menor preço, maior desconto, melhor técnica ou conteúdo artístico, maior retorno ' +
      'econômico (art. 33). Exige Plano de Contratações Anual, Estudo Técnico Preliminar, matriz de riscos. Portal Nacional de Contratações Públicas ' +
      '(PNCP, art. 174). Governança e integridade: programa de integridade obrigatório para contratos de grande vulto (art. 25, §4º).',
  },
  '13709/2018': {
    title: 'Lei Geral de Proteção de Dados Pessoais (LGPD)',
    summary: 'Regula o tratamento de dados pessoais no Brasil, inspirada no RGPD europeu — bases legais, direitos do titular, ANPD e sanções.',
    content:
      'Bases legais para tratamento de dados (art. 7º): consentimento, cumprimento de obrigação legal, execução de contrato, legítimo interesse, entre ' +
      'outras. Dados sensíveis exigem base legal específica (art. 11). Direitos do titular: confirmação, acesso, correção, anonimização, portabilidade, ' +
      'eliminação, revogação do consentimento (art. 18). Agentes de tratamento: controlador e operador, com responsabilidade solidária (arts. 42-45). ' +
      'Autoridade Nacional de Proteção de Dados (ANPD) — fiscalização e sanções administrativas de até 2% do faturamento, limitadas a R$ 50 milhões por ' +
      'infração (art. 52). Relatório de Impacto à Proteção de Dados (RIPD) em tratamentos de alto risco.',
  },
  '5452/1943': {
    title: 'Consolidação das Leis do Trabalho (CLT)',
    summary: 'Principal diploma trabalhista brasileiro — contrato de trabalho, jornada, remuneração, férias, segurança do trabalho e Justiça do Trabalho.',
    content:
      'Contrato individual de trabalho: caracterização de vínculo empregatício — subordinação, pessoalidade, onerosidade, não eventualidade (arts. 2º-3º). ' +
      'Jornada de trabalho: limite de 8h diárias/44h semanais, horas extras, intervalos (arts. 58-71). Remuneração: salário mínimo, 13º salário (Lei ' +
      '4.090/62), equiparação salarial (art. 461). Férias anuais remuneradas de 30 dias (arts. 129-153). Segurança e medicina do trabalho (arts. 154-201). ' +
      'Rescisão contratual: justa causa, aviso prévio, FGTS (Lei 8.036/90 complementa). Reformada substancialmente pela Lei 13.467/2017 (Reforma ' +
      'Trabalhista) — trabalho intermitente, prevalência do negociado sobre o legislado em certos temas, extinção da contribuição sindical obrigatória.',
  },
  '8213/1991': {
    title: 'Lei de Benefícios da Previdência Social',
    summary: 'Disciplina os benefícios do Regime Geral de Previdência Social (RGPS): aposentadorias, auxílios, pensão por morte e salário-família.',
    content:
      'Beneficiários: segurados obrigatórios e facultativos, dependentes (arts. 11-16). Benefícios: aposentadoria por idade, por tempo de contribuição ' +
      '(regras de transição pós-EC 103/2019), por invalidez; auxílio-doença, auxílio-acidente; pensão por morte; salário-maternidade; salário-família ' +
      '(arts. 18-92). Carências mínimas de contribuição por benefício (art. 25). Cálculo da renda mensal inicial com base no salário de benefício (arts. ' +
      '28-29). Acidente do trabalho e doenças ocupacionais (arts. 19-23).',
  },
  '5172/1966': {
    title: 'Código Tributário Nacional (CTN)',
    summary: 'Normas gerais de direito tributário: competência tributária, espécies de tributos, obrigação e crédito tributário, prescrição e decadência.',
    content:
      'Sistema Tributário Nacional: competência da União, Estados, DF e Municípios (arts. 6º-15). Espécies tributárias: impostos, taxas, contribuições de ' +
      'melhoria (arts. 16-82). Obrigação tributária principal e acessória, fato gerador (arts. 113-118). Crédito tributário: constituição por lançamento ' +
      '(arts. 142-150), suspensão (moratória, depósito, liminar — art. 151), extinção (pagamento, compensação, prescrição em 5 anos — art. 156/174), ' +
      'exclusão (isenção, anistia — art. 175). Recepcionado com status de lei complementar pela Constituição de 1988.',
  },
  '8078/1990': {
    title: 'Código de Defesa do Consumidor (CDC)',
    summary: 'Protege o consumidor nas relações de consumo: direitos básicos, responsabilidade por vício e defeito, práticas comerciais e proteção contratual.',
    content:
      'Direitos básicos do consumidor: proteção à vida e saúde, informação adequada, proteção contratual, facilitação da defesa em juízo com inversão do ' +
      'ônus da prova (art. 6º). Responsabilidade objetiva do fornecedor por fato do produto/serviço (arts. 12-17) e por vício de qualidade (arts. 18-25) — ' +
      'prazos decadenciais de 30 (não duráveis) e 90 dias (duráveis) para reclamar (art. 26). Práticas comerciais: oferta, publicidade enganosa/abusiva, ' +
      'práticas abusivas, cobrança de dívidas, bancos de dados (arts. 29-44). Proteção contratual: cláusulas abusivas nulas de pleno direito (art. 51), ' +
      'direito de arrependimento em compras fora do estabelecimento comercial em 7 dias (art. 49).',
  },
  '6015/1973': {
    title: 'Lei de Registros Públicos',
    summary: 'Regula os registros públicos no Brasil: registro civil de pessoas naturais, registro de imóveis e demais serventias extrajudiciais.',
    content:
      'Registro civil de pessoas naturais: nascimento, casamento, óbito, natimorto (arts. 29-80). Registro de imóveis: matrícula, princípio da ' +
      'continuidade, publicidade registral, usucapião extrajudicial (arts. 167-288 e art. 216-A, incluído pela Lei 11.977/2009). Registro de títulos e ' +
      'documentos, registro civil de pessoas jurídicas (arts. 114-136). Base do princípio da fé pública registral no direito imobiliário brasileiro.',
  },
  '10257/2001': {
    title: 'Estatuto da Cidade',
    summary: 'Regulamenta os arts. 182 e 183 da Constituição — política urbana, plano diretor, função social da propriedade e instrumentos de gestão urbana.',
    content:
      'Diretrizes gerais da política urbana: função social da cidade e da propriedade (arts. 1º-3º). Instrumentos: plano diretor obrigatório para ' +
      'municípios com mais de 20 mil habitantes (arts. 39-42); parcelamento, edificação ou utilização compulsórios; IPTU progressivo no tempo; ' +
      'desapropriação com pagamento em títulos (arts. 5º-8º); usucapião especial urbana coletiva (arts. 9º-14); direito de superfície, outorga onerosa do ' +
      'direito de construir, operações urbanas consorciadas (arts. 21-33). Gestão democrática da cidade com participação popular obrigatória (art. 43).',
  },
  '0/1988': {
    title: 'Constituição da República Federativa do Brasil',
    summary: 'Lei fundamental do Estado brasileiro — direitos fundamentais, organização do Estado, dos Poderes e ordem econômica/social.',
    content:
      'Título I — Princípios Fundamentais (arts. 1º-4º): Estado Democrático de Direito, soberania, cidadania, dignidade da pessoa humana. Título II — ' +
      'Direitos e Garantias Fundamentais (arts. 5º-17): direitos individuais e coletivos, direitos sociais, nacionalidade, direitos políticos. Título III ' +
      '— Organização do Estado (arts. 18-43): União, Estados, Municípios, DF. Título IV — Organização dos Poderes (arts. 44-135): Legislativo, ' +
      'Executivo, Judiciário, funções essenciais à Justiça. Título VII — Ordem Econômica e Financeira (arts. 170-192); Título VIII — Ordem Social ' +
      '(arts. 193-232): seguridade social, educação, cultura, meio ambiente, família. Usucapião especial urbana (art. 183) e rural (art. 191).',
  },
};

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
