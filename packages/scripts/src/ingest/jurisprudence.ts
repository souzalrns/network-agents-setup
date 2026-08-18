// scripts/ingest/jurisprudence.ts
//
// NOTA DE FIDELIDADE (histórico): o material originalmente colado tinha ingestSTJ/ingestTJSP/
// ingestPortugueseTribunals como stubs sem gravar nada real. Uma versão posterior implementou
// a busca de rede real (com fallback simulado) — mas usava NÚMEROS DE PROCESSO INVENTADOS
// (ex.: "RE-123456-7", "REsp-1234567") anexados a um texto de decisão genérico gerado por
// template ("Decisão do STF sobre RE-123456-7"). Isso é mais perigoso do que um placeholder
// óbvio: parece uma citação real, mas é fabricada — um sistema jurídico não deveria "inventar"
// jurisprudência com aparência de real.
//
// REVISÃO 18/08/2026 — substituído por um conjunto pequeno de casos REAIS e VERIFICADOS
// (busca contra fontes: portal STF, TJDFT, Sérvulo & Associados) em vez de uma lista maior
// de números fabricados. Cada entrada abaixo tem o número de processo/súmula real e um
// resumo fiel ao que foi decidido — não é o acórdão literal (que não foi buscado
// integralmente), é uma síntese verificada. Melhor uma lista menor e correta do que uma
// maior com números inventados.

import { prisma } from '../db';

interface JurisprudenceData {
  court: string;
  caseNumber: string;
  jurisdiction: 'BR' | 'PT';
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

    console.log('⚖️ Ingerindo jurisprudência (conjunto curado e verificado)...');

    for (const data of this.getCuratedCases()) {
      total++;
      try {
        const result = await this.saveJurisprudence(data);
        if (result === 'inserted') inserted++;
        else if (result === 'updated') updated++;
      } catch (error) {
        errors++;
        console.error(`  ❌ Erro ${data.court} ${data.caseNumber}:`, error);
      }
    }

    console.log(`✅ Jurisprudência: ${total} processos (${inserted} inseridos, ${updated} atualizados, ${errors} erros)`);

    return { total, inserted, updated, errors };
  }

  private static getCuratedCases(): JurisprudenceData[] {
    const now = new Date().toISOString();

    return [
      {
        court: 'STF',
        caseNumber: 'ADI 4277 / ADPF 132',
        jurisdiction: 'BR',
        date: '2011-05-05',
        summary: 'STF reconhece a união homoafetiva como entidade familiar, com os mesmos direitos e deveres da união estável heteroafetiva.',
        content:
          'Julgamento conjunto da ADI 4277 e da ADPF 132, relator Min. Ayres Britto, em 05/05/2011. O STF deu interpretação conforme a Constituição ao ' +
          'art. 1.723 do Código Civil para reconhecer a união entre pessoas do mesmo sexo como entidade familiar, aplicando-se as mesmas regras e ' +
          'consequências da união estável heteroafetiva.',
        decision: 'Procedente por unanimidade — reconhecimento da união homoafetiva como entidade familiar.',
        url: 'https://portal.stf.jus.br/peticaoInicial/verPeticaoInicial.asp?base=ADI&numProcesso=4277',
        source: 'stf',
        tags: ['stf', 'jurisprudencia', 'brasil', 'familia', 'uniao-estavel'],
        metadata: { fetchedAt: now, court: 'STF', isReal: true, isCurated: true },
      },
      {
        court: 'STF',
        caseNumber: 'RE 898.060 (Tema 622 - Repercussão Geral)',
        jurisdiction: 'BR',
        date: '2016-09-21',
        summary: 'STF fixa tese de repercussão geral admitindo a multiparentalidade: coexistência da paternidade biológica e socioafetiva com efeitos jurídicos próprios.',
        content:
          'Relator Min. Luiz Fux. Tese fixada (Tema 622): "A paternidade socioafetiva, declarada ou não em registro público, não impede o ' +
          'reconhecimento do vínculo de filiação concomitante baseado na origem biológica, com os efeitos jurídicos próprios."',
        decision: 'Tese de repercussão geral fixada — possibilidade de multiparentalidade.',
        url: 'https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=622',
        source: 'stf',
        tags: ['stf', 'jurisprudencia', 'brasil', 'familia', 'filiacao'],
        metadata: { fetchedAt: now, court: 'STF', isReal: true, isCurated: true },
      },
      {
        court: 'STF',
        caseNumber: 'Súmula Vinculante 13',
        jurisdiction: 'BR',
        date: '2008-08-21',
        summary: 'Veda o nepotismo na Administração Pública direta e indireta, em qualquer dos Poderes da União, Estados, DF e Municípios.',
        content:
          'Texto: "A nomeação de cônjuge, companheiro ou parente em linha reta, colateral ou por afinidade, até o terceiro grau, inclusive, da autoridade ' +
          'nomeante ou de servidor da mesma pessoa jurídica investido em cargo de direção, chefia ou assessoramento, para o exercício de cargo em ' +
          'comissão ou de confiança ou, ainda, de função gratificada na administração pública direta e indireta em qualquer dos poderes da União, dos ' +
          'Estados, do Distrito Federal e dos Municípios, compreendido o ajuste mediante designações recíprocas, viola a Constituição Federal."',
        decision: 'Súmula vinculante aprovada — nepotismo declarado inconstitucional independentemente de lei específica.',
        url: 'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=30&sumula=1207',
        source: 'stf',
        tags: ['stf', 'jurisprudencia', 'brasil', 'administrativo', 'nepotismo'],
        metadata: { fetchedAt: now, court: 'STF', isReal: true, isCurated: true },
      },
      {
        court: 'STJ',
        caseNumber: 'Súmula 385',
        jurisdiction: 'BR',
        date: '2009-06-27',
        summary: 'A anotação irregular em cadastro de proteção ao crédito não gera dano moral quando já existe inscrição anterior legítima, ressalvado o direito ao cancelamento.',
        content:
          'Texto: "Da anotação irregular em cadastro de proteção ao crédito, não cabe indenização por dano moral, quando preexistente legítima ' +
          'inscrição, ressalvado o direito ao cancelamento." Consolidação de entendimento do STJ em matéria de direito do consumidor e responsabilidade ' +
          'civil por negativação indevida.',
        decision: 'Súmula editada consolidando jurisprudência das Turmas de Direito Privado do STJ.',
        url: 'https://www.stj.jus.br/',
        source: 'stj',
        tags: ['stj', 'jurisprudencia', 'brasil', 'consumidor', 'dano-moral'],
        metadata: { fetchedAt: now, court: 'STJ', isReal: true, isCurated: true },
      },
      {
        court: 'STJ',
        caseNumber: 'Súmula 7',
        jurisdiction: 'BR',
        date: '1990-06-28',
        summary: 'Não cabe recurso especial quando o acórdão recorrido exigiria reexame de prova para ser revisto.',
        content:
          'Texto: "A pretensão de simples reexame de prova não enseja recurso especial." Súmula processual amplamente aplicada para não conhecer ' +
          'recursos especiais que, na prática, pretendem nova valoração de fatos e provas já apreciados pelas instâncias ordinárias.',
        decision: 'Súmula editada — natureza estritamente processual/procedimental do recurso especial.',
        url: 'https://www.stj.jus.br/',
        source: 'stj',
        tags: ['stj', 'jurisprudencia', 'brasil', 'processual', 'recurso-especial'],
        metadata: { fetchedAt: now, court: 'STJ', isReal: true, isCurated: true },
      },
      {
        court: 'STJ Portugal',
        caseNumber: 'Acórdão Uniformizador de Jurisprudência n.º 6/2023',
        jurisdiction: 'PT',
        date: '2023-07-13',
        summary: 'STJ português uniformiza a interpretação do art. 50.º do NRAU sobre requisitos de comunicação na transição de arrendamentos para o novo regime sem atualização de renda.',
        content:
          'Matéria: interpretação do art. 50.º do Novo Regime do Arrendamento Urbano (NRAU), sobre os requisitos exigidos na comunicação de transição de ' +
          'contratos de arrendamento para fins não habitacionais. Tese fixada: o proprietário que pretenda promover a transição para o NRAU SEM ' +
          'atualizar a renda não é obrigado a indicar o valor do imóvel nem a enviar cópia da caderneta predial urbana (alíneas b e c do art. 50.º) — ' +
          'esses elementos só são essenciais quando há atualização simultânea da renda. Acórdão obteve 11 votos de vencido.',
        decision: 'Uniformização de jurisprudência fixada em 13/07/2023.',
        url: 'https://www.stj.pt/uniformizacao-de-jurisprudencia/civel/',
        source: 'stj-pt',
        tags: ['stj-pt', 'jurisprudencia', 'portugal', 'arrendamento'],
        metadata: { fetchedAt: now, court: 'STJ Portugal', isReal: true, isCurated: true },
      },
    ];
  }

  private static async saveJurisprudence(data: JurisprudenceData): Promise<'inserted' | 'updated'> {
    const existing = await prisma.legalDocument.findFirst({
      where: { source: data.source, number: data.caseNumber },
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
        title: `${data.court} - ${data.caseNumber}`,
        type: 'jurisprudencia',
        jurisdiction: data.jurisdiction,
        number: data.caseNumber,
        year: data.date.slice(0, 4),
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
