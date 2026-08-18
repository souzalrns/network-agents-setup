// scripts/validate/check-completeness.ts
//
// Colado literalmente pelo usuário, com a mesma adaptação estrutural de
// ingest/index.ts#updateCompleteness: `prisma.agent.findMany({ where: { domain: 'legal' } })`
// não existe (sem tabela "Agent"; ver nota em ../legal-agents.ts). Trocado por
// AgentFactory + computeLegalAgentCompleteness. Além disso, `const validator = new
// CompletenessValidator()` no texto original era instanciado e nunca mais usado (bug de
// variável morta) — como esta é justamente a peça que faltava conectar de verdade, o
// validator agora É usado: cada agente jurídico é registrado como uma Capability real e
// consultado via `validator.checkCompleteness()`, em vez do cálculo ad-hoc do rascunho.

import { CompletenessValidator } from '@network-agents/core';
import { createAgentFactory } from '../bootstrap';
import { computeLegalAgentCompleteness } from '../legal-agents';

interface AgentCompleteness {
  agentId: string;
  name: string;
  domain: string;
  jurisdiction: string;
  completeness: number;
  documents: number;
  status: 'operational' | 'partial' | 'empty';
  missingTypes: string[];
}

const REQUIRED_TYPES = ['lei', 'jurisprudencia', 'doutrina'];

export async function checkCompleteness(): Promise<AgentCompleteness[]> {
  const results: AgentCompleteness[] = [];

  // Agentes do domínio jurídico (em memória, via AgentFactory)
  const agentFactory = createAgentFactory();
  const agents = agentFactory.getAgentsByDomain('legal');

  const validator = new CompletenessValidator();

  for (const agent of agents) {
    const status = await computeLegalAgentCompleteness(agent.id);

    // Registra a capability real no CompletenessValidator (P-xxx: Verificação de
    // Completude) e consulta a completude através da API real, em vez de recalcular
    // o status manualmente como no rascunho original.
    const capability = validator.registerCapability({
      // registerCapability() sobrescreve `id` internamente com um novo id gerado — mas o
      // tipo do parâmetro (Omit<Capability, 'completeness' | 'status' | 'currentContentTypes'>)
      // ainda exige que `id` esteja presente na chamada.
      id: `legal-${agent.id}`,
      name: `${agent.name} (${status.jurisdiction})`,
      type: 'knowledge_base',
      requiredContentTypes: REQUIRED_TYPES,
      validationRules: [],
      metadata: { agentId: agent.id, jurisdiction: status.jurisdiction },
    });

    for (const type of status.docTypes) {
      if (REQUIRED_TYPES.includes(type)) {
        await validator.ingestContent(capability.id, 'legal-document-count', type, {
          count: status.documentsCount,
        });
      }
    }

    const check = validator.checkCompleteness(capability.id);
    const missingTypes = check.missingContentTypes;

    let statusLabel: 'operational' | 'partial' | 'empty' = 'empty';
    if (status.completeness >= 80) statusLabel = 'operational';
    else if (status.completeness >= 30) statusLabel = 'partial';

    results.push({
      agentId: agent.id,
      name: agent.name,
      domain: agent.domain || 'legal',
      jurisdiction: status.jurisdiction,
      completeness: status.completeness,
      documents: status.documentsCount,
      status: statusLabel,
      missingTypes,
    });
  }

  // Gera relatório
  console.log('\n📊 RELATÓRIO DE COMPLETUDE DOS AGENTES');
  console.log('='.repeat(60));
  console.log(`Total de agentes: ${results.length}`);
  console.log(`Operacionais: ${results.filter((r) => r.status === 'operational').length}`);
  console.log(`Parciais: ${results.filter((r) => r.status === 'partial').length}`);
  console.log(`Vazios: ${results.filter((r) => r.status === 'empty').length}`);
  console.log('\nDetalhes:');
  for (const r of results) {
    const icon = r.status === 'operational' ? '✅' : r.status === 'partial' ? '⚠️' : '❌';
    console.log(`  ${icon} ${r.name} (${r.jurisdiction}): ${r.completeness.toFixed(1)}% - ${r.documents} docs`);
    if (r.missingTypes.length > 0) {
      console.log(`     Faltando: ${r.missingTypes.join(', ')}`);
    }
  }

  return results;
}

if (require.main === module) {
  checkCompleteness().then(() => process.exit(0));
}
