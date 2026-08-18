// scripts/ingest/index.ts
//
// Colado literalmente pelo usuário, com uma única mudança estrutural: o método
// `updateCompleteness()` original fazia `prisma.agent.findMany({ where: { domain: 'legal' } })`
// e `prisma.agent.update(...)` — não existe tabela "Agent" no schema real (agentes são
// geridos em memória por AgentFactory). Foi adaptado para usar AgentFactory +
// computeLegalAgentCompleteness (ver ../legal-agents.ts). O resto (estrutura da classe,
// logs, ordem dos passos) é o texto original.

import { BrazilianLawIngestor } from './brazilian-law';
import { PortugueseLawIngestor } from './portuguese-law';
import { JurisprudenceIngestor } from './jurisprudence';
import { DoctrineIngestor } from './doctrine';
import { EmbeddingGenerator } from './embeddings';
import { getGlobalLogger } from '@network-agents/observability';
import { createAgentFactory } from '../bootstrap';
import { computeLegalAgentCompleteness } from '../legal-agents';

const logger = getGlobalLogger();

interface IngestStats {
  total: number;
  inserted: number;
  updated: number;
  errors: number;
  details: Array<{ source: string; count: number }>;
}

export class InitialIngestion {
  static async run(): Promise<IngestStats> {
    const stats: IngestStats = {
      total: 0,
      inserted: 0,
      updated: 0,
      errors: 0,
      details: [],
    };

    console.log('🚀 Iniciando ingestão inicial de conhecimento jurídico...');
    console.log('='.repeat(60));

    // 1. Leis Brasileiras
    console.log('\n📜 Ingerindo leis brasileiras...');
    const brLaws = await BrazilianLawIngestor.ingestAll();
    stats.total += brLaws.total;
    stats.inserted += brLaws.inserted;
    stats.updated += brLaws.updated;
    stats.errors += brLaws.errors;
    stats.details.push({ source: 'Leis BR', count: brLaws.inserted });

    // 2. Leis Portuguesas
    console.log('\n📜 Ingerindo leis portuguesas...');
    const ptLaws = await PortugueseLawIngestor.ingestAll();
    stats.total += ptLaws.total;
    stats.inserted += ptLaws.inserted;
    stats.updated += ptLaws.updated;
    stats.errors += ptLaws.errors;
    stats.details.push({ source: 'Leis PT', count: ptLaws.inserted });

    // 3. Jurisprudência
    console.log('\n⚖️ Ingerindo jurisprudência...');
    const juris = await JurisprudenceIngestor.ingestAll();
    stats.total += juris.total;
    stats.inserted += juris.inserted;
    stats.updated += juris.updated;
    stats.errors += juris.errors;
    stats.details.push({ source: 'Jurisprudência', count: juris.inserted });

    // 4. Doutrina (se disponível)
    console.log('\n📚 Ingerindo doutrina...');
    const doctrine = await DoctrineIngestor.ingestAll();
    stats.total += doctrine.total;
    stats.inserted += doctrine.inserted;
    stats.updated += doctrine.updated;
    stats.errors += doctrine.errors;
    stats.details.push({ source: 'Doutrina', count: doctrine.inserted });

    // 5. Gerar embeddings
    console.log('\n🧠 Gerando embeddings...');
    const embedStats = await EmbeddingGenerator.generateAll();
    stats.details.push({ source: 'Embeddings', count: embedStats.processed });

    // 6. Atualizar completude
    console.log('\n✅ Atualizando status de completude...');
    await this.updateCompleteness();

    // 7. Relatório final
    console.log('\n' + '='.repeat(60));
    console.log('📊 RELATÓRIO DE INGESTÃO');
    console.log('='.repeat(60));
    console.log(`Total processado: ${stats.total}`);
    console.log(`Inseridos: ${stats.inserted}`);
    console.log(`Atualizados: ${stats.updated}`);
    console.log(`Erros: ${stats.errors}`);
    console.log('\nDetalhes:');
    for (const detail of stats.details) {
      console.log(`  ${detail.source}: ${detail.count}`);
    }
    console.log('\n🎉 Ingestão concluída!');

    return stats;
  }

  private static async updateCompleteness(): Promise<void> {
    // Agentes do domínio jurídico (em memória, via AgentFactory — não existe tabela
    // "Agent" no banco; ver nota de fidelidade no topo do arquivo).
    const agentFactory = createAgentFactory();
    const agents = agentFactory.getAgentsByDomain('legal');

    for (const agent of agents) {
      const status = await computeLegalAgentCompleteness(agent.id);
      logger.info(
        `[InitialIngestion] ${agent.id} (${status.jurisdiction}): ${status.completeness.toFixed(1)}% - ${status.documentsCount} docs`
      );
    }
  }
}

// Executa se for chamado diretamente
if (require.main === module) {
  InitialIngestion.run()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('❌ Erro na ingestão:', error);
      process.exit(1);
    });
}
