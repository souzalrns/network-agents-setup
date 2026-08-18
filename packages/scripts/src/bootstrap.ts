/**
 * NOTA DE FIDELIDADE: este módulo não existia no material colado pelo usuário.
 * Os scripts originais de validação (`check-completeness.ts` e `test-agents.ts`)
 * assumiam:
 *   1. uma tabela Prisma "Agent" (`prisma.agent.findMany({ where: { domain: 'legal' } })`)
 *      que não existe no schema real — os agentes são inteiramente em memória, geridos
 *      por AgentFactory (ver packages/core/src/agents/AgentFactory.ts);
 *   2. `new Orchestrator(/* ... *\/)` sem argumentos, que não compila — o construtor real
 *      exige (agentFactory, router, planner, executor, memory, hitlManager).
 *
 * Este bootstrap centraliza a composição real da plataforma, replicando exatamente a
 * mesma cadeia de construção usada em apps/api/src/index.ts, para que os scripts de
 * ingestão/validação usem um AgentFactory/Orchestrator/CompletenessValidator de verdade
 * em vez de placeholders.
 */
import {
  AgentFactory,
  Orchestrator,
  Router,
  Planner,
  Executor,
  LLMService,
  OpenAIProvider,
  HitlManager,
} from '@network-agents/core';
import { MemoryManager } from '@network-agents/memory';
import { getGlobalLogger } from '@network-agents/observability';
import { AGENT_CONFIGS } from '../../../config/agents.config';

export interface Bootstrapped {
  agentFactory: AgentFactory;
  orchestrator: Orchestrator;
  memory: MemoryManager;
}

/**
 * Constrói apenas o AgentFactory (sem o resto da plataforma). Usado pelos scripts que só
 * precisam consultar quais agentes existem (ex.: ingest/index.ts, validate/check-completeness.ts)
 * sem pagar o custo de instanciar um Orchestrator inteiro.
 */
export function createAgentFactory(): AgentFactory {
  const logger = getGlobalLogger();
  const agentFactory = new AgentFactory({ publicMode: false });
  AGENT_CONFIGS.forEach((config) => agentFactory.registerAgent(config));
  logger.info(`[scripts/bootstrap] Agents loaded: ${agentFactory.getAllAgents().length}`);
  return agentFactory;
}

export function bootstrap(): Bootstrapped {
  const agentFactory = createAgentFactory();

  const memory = new MemoryManager({
    redisUrl: process.env.REDIS_URL,
    cacheTTL: 3600,
  });

  const hitlManager = new HitlManager({
    autoExpireMinutes: parseInt(process.env.HITL_EXPIRE_MINUTES || '60'),
  });

  const llmProvider = new OpenAIProvider(
    process.env.OPENAI_API_KEY || '',
    process.env.DEFAULT_MODEL || 'gpt-4-turbo'
  );
  const llm = new LLMService(llmProvider);

  const router = new Router();
  const planner = new Planner(agentFactory, llm);
  const executor = new Executor(agentFactory, memory, llm, hitlManager);

  const orchestrator = new Orchestrator(
    agentFactory,
    router,
    planner,
    executor,
    memory,
    hitlManager
  );

  return { agentFactory, orchestrator, memory };
}

/** IDs dos agentes de domínio "legal" já cadastrados em config/agents.config.ts */
export const LEGAL_AGENT_IDS = [
  'legal-orchestrator',
  'civil-law-br',
  'civil-law-pt',
  'legal-research',
] as const;
