/**
 * NOTA DE FIDELIDADE: módulo novo, não fazia parte do material colado pelo usuário.
 *
 * O material original (scripts/ingest/index.ts#updateCompleteness e
 * scripts/validate/check-completeness.ts#checkCompleteness) assumia uma tabela Prisma
 * "Agent" (`prisma.agent.findMany({ where: { domain: 'legal' } })` /
 * `prisma.agent.update(...)`) usada para guardar, por agente, a jurisdição e a
 * completude calculada em `agent.metadata`. Essa tabela não existe — agentes são
 * inteiramente em memória via AgentFactory (packages/core/src/agents/AgentFactory.ts) e
 * não têm um campo `metadata` gravável.
 *
 * Este módulo concentra a única peça de informação que faltava (a jurisdição de cada
 * agente jurídico) e centraliza o cálculo de completude real a partir dos documentos
 * efetivamente ingeridos em LegalDocument, para os dois scripts que dependiam de
 * "prisma.agent".
 */
import { prisma } from './db';

export interface LegalAgentCompleteness {
  agentId: string;
  jurisdiction: 'BR' | 'PT';
  completeness: number;
  documentsCount: number;
  docTypes: string[];
  lastUpdated: Date;
}

// Os 4 agentes de domínio 'legal' já cadastrados em config/agents.config.ts.
// legal-orchestrator e legal-research atendem as duas jurisdições; usamos 'BR' como
// jurisdição primária de referência para o relatório de completude de ambos.
const JURISDICTION_BY_AGENT: Record<string, 'BR' | 'PT'> = {
  'civil-law-br': 'BR',
  'civil-law-pt': 'PT',
  'legal-orchestrator': 'BR',
  'legal-research': 'BR',
};

export function getLegalAgentJurisdiction(agentId: string): 'BR' | 'PT' {
  return JURISDICTION_BY_AGENT[agentId] || 'BR';
}

export async function computeLegalAgentCompleteness(agentId: string): Promise<LegalAgentCompleteness> {
  const jurisdiction = getLegalAgentJurisdiction(agentId);

  const docCounts = await prisma.legalDocument.groupBy({
    by: ['type'],
    where: { jurisdiction },
    _count: true,
  });

  const documentsCount = docCounts.reduce((sum: number, d: any) => sum + d._count, 0);

  // Mesma heurística usada no material original colado pelo usuário
  // (scripts/ingest/index.ts#updateCompleteness): presença de qualquer tipo de
  // documento já ingerido é tratada como "quase operacional". É um placeholder
  // deliberadamente simples, não uma medida real de qualidade do conteúdo.
  const completeness = docCounts.length > 0 ? 80 + Math.random() * 20 : 20;

  return {
    agentId,
    jurisdiction,
    completeness,
    documentsCount,
    docTypes: docCounts.map((d: any) => d.type),
    lastUpdated: new Date(),
  };
}
