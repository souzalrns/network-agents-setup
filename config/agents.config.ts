import { AgentConfig } from '@network-agents/shared';
export const AGENT_CONFIGS: AgentConfig[] = [
  // ========== META (Camada 1) ==========
  {
    id: 'orchestrator-general',
    layer: 'meta',
    visibility: 'public',
    description: 'Ponto de entrada de todas as demandas, roteia para o domínio correto.',
  },
  {
    id: 'domain-router',
    layer: 'meta',
    visibility: 'public',
    description: 'Identifica se a demanda é de Software, Medicina, Marketing, Construção, Direito, etc.',
  },
  {
    id: 'context-manager',
    layer: 'meta',
    visibility: 'public',
    description: 'Mantém o histórico e estado da conversa/projeto.',
  },
  {
    id: 'task-planner',
    layer: 'meta',
    visibility: 'public',
    description: 'Quebra demandas complexas em subtarefas.',
  },
  // ========== HORIZONTAL (Skills) ==========
  {
    id: 'research-agent',
    layer: 'horizontal',
    visibility: 'public',
    description: 'Pesquisa genérica (mercado, técnica, jurídica, médica…).',
  },
  {
    id: 'critic-validator',
    layer: 'horizontal',
    visibility: 'public',
    description: 'Revisa qualidade de qualquer saída.',
  },
  {
    id: 'documentation-agent',
    layer: 'horizontal',
    visibility: 'public',
    description: 'Gera textos, relatórios e documentação.',
  },
  {
    id: 'methodology-legal',
    layer: 'horizontal',
    visibility: 'public',
    description: 'Raciocínio jurídico genérico (fato × direito, hermenêutica).',
  },
  // ========== VERTICAL - BUSINESS ==========
  {
    id: 'lead-qualifier',
    layer: 'vertical',
    visibility: 'private',
    domain: 'business',
    description: 'Analisa e qualifica oportunidades comerciais.',
  },
  {
    id: 'proposal-agent',
    layer: 'vertical',
    visibility: 'private',
    domain: 'business',
    description: 'Gera cotações e propostas comerciais.',
  },
  {
    id: 'financial-analyst',
    layer: 'vertical',
    visibility: 'private',
    domain: 'business',
    description: 'Análise financeira, contas a pagar/receber, conciliação.',
  },
  // ========== VERTICAL - MEDICAL ==========
  {
    id: 'clinical-orchestrator',
    layer: 'vertical',
    visibility: 'private',
    domain: 'medical',
    description: 'Coordena casos e fluxos clínicos.',
  },
  {
    id: 'triage-agent',
    layer: 'vertical',
    visibility: 'private',
    domain: 'medical',
    description: 'Classificação de risco (Protocolo de Manchester).',
  },
  {
    id: 'cardiologist-agent',
    layer: 'vertical',
    visibility: 'private',
    domain: 'medical',
    description: 'Avaliação e conduta cardiológica.',
  },
  // ========== VERTICAL - MARKETING ==========
  {
    id: 'marketing-orchestrator',
    layer: 'vertical',
    visibility: 'private',
    domain: 'marketing',
    description: 'Recebe briefings e controla o fluxo criativo.',
  },
  {
    id: 'copywriter-agent',
    layer: 'vertical',
    visibility: 'private',
    domain: 'marketing',
    description: 'Headlines, textos de anúncios, scripts, storytelling.',
  },
  {
    id: 'geo-agent',
    layer: 'vertical',
    visibility: 'private',
    domain: 'marketing',
    description: 'Generative Engine Optimization — posicionamento em pesquisas de IA.',
  },
  // ========== VERTICAL - CONSTRUCTION ==========
  {
    id: 'construction-orchestrator',
    layer: 'vertical',
    visibility: 'private',
    domain: 'construction',
    description: 'Organiza etapas e fluxo da obra/reforma.',
  },
  {
    id: 'architect-agent',
    layer: 'vertical',
    visibility: 'private',
    domain: 'construction',
    description: 'Plantas, layouts, fluxos, estética e soluções de espaço.',
  },
  {
    id: 'civil-engineer',
    layer: 'vertical',
    visibility: 'private',
    domain: 'construction',
    description: 'Cálculo estrutural, fundações, estabilidade, lajes, vigas e pilares.',
  },
  // ========== VERTICAL - LEGAL ==========
  {
    id: 'legal-orchestrator',
    layer: 'vertical',
    visibility: 'private',
    domain: 'legal',
    description: 'Recebe a questão, identifica a jurisdição, decompõe o problema.',
  },
  {
    // F1: profile substitui a duplicação de texto entre civil-law-br/-pt --
    // mesmo systemPrompt-template, só o profile muda. IDs mantidos (não
    // fundidos numa única entrada): SpecialtyManager.ts, bootstrap.ts,
    // legal-agents.ts e check-consistency.ts referenciam estes 2 IDs
    // directamente -- fundir exigia alterar os 4, fora do escopo deste item.
    id: 'civil-law-br',
    layer: 'vertical',
    visibility: 'private',
    domain: 'legal',
    description: 'Direito Civil Brasileiro (contratos, responsabilidade civil, família).',
    systemPrompt: 'Direito Civil {{jurisdiction_label}} (contratos, responsabilidade civil, família).',
    profile: { jurisdiction: 'BR', jurisdiction_label: 'Brasileiro' },
  },
  {
    id: 'civil-law-pt',
    layer: 'vertical',
    visibility: 'private',
    domain: 'legal',
    description: 'Direito Civil Português (contratos, responsabilidade civil, família).',
    systemPrompt: 'Direito Civil {{jurisdiction_label}} (contratos, responsabilidade civil, família).',
    profile: { jurisdiction: 'PT', jurisdiction_label: 'Português' },
  },
  {
    id: 'legal-research',
    layer: 'horizontal',
    visibility: 'public',
    domain: 'legal',
    description: 'Busca legislação, jurisprudência e doutrina com filtro por país.',
  },
];
