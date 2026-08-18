import { getGlobalLogger } from '@network-agents/observability';
import { AgentFactory } from '../agents/AgentFactory';

// P-057 a P-060: Gestão de Especialidades — define especialidades de
// domínio (conhecimento, ferramentas, agentes) e materializa os agentes
// correspondentes via AgentFactory.

export interface Specialty {
  id: string;
  name: string;
  domain: string;
  knowledgeAreas: string[];
  tools: string[];
  agentIds: string[];
  createdAt: Date;
}

const DEFAULT_SPECIALTIES: Array<Omit<Specialty, 'id' | 'agentIds' | 'createdAt'>> = [
  {
    name: 'Jurídico',
    domain: 'legal',
    knowledgeAreas: ['contratos', 'compliance', 'legislação civil'],
    tools: ['document_search', 'contract_analyzer'],
  },
  {
    name: 'HVAC',
    domain: 'hvac',
    knowledgeAreas: ['climatização', 'manutenção preventiva', 'normas técnicas'],
    tools: ['diagnostic_checklist', 'maintenance_scheduler'],
  },
  {
    name: 'Construção',
    domain: 'construction',
    knowledgeAreas: ['orçamento de obras', 'normas ABNT', 'gestão de projetos'],
    tools: ['budget_estimator', 'project_tracker'],
  },
  {
    name: 'Marketing',
    domain: 'marketing',
    knowledgeAreas: ['SEO', 'copywriting', 'análise de campanhas'],
    tools: ['content_generator', 'campaign_analyzer'],
  },
  {
    name: 'Medicina',
    domain: 'medicine',
    knowledgeAreas: ['triagem', 'protocolos clínicos', 'terminologia médica'],
    tools: ['symptom_checker', 'medical_reference'],
  },
];

export class SpecialtyManager {
  private specialties: Map<string, Specialty> = new Map();
  private logger = getGlobalLogger();

  constructor(private agentFactory: AgentFactory) {
    this.registerDefaultSpecialties();
  }

  private registerDefaultSpecialties(): void {
    for (const spec of DEFAULT_SPECIALTIES) {
      this.registerSpecialty(spec);
    }
  }

  registerSpecialty(params: Omit<Specialty, 'id' | 'agentIds' | 'createdAt'>): Specialty {
    const id = `spec_${params.domain}`;
    const specialty: Specialty = {
      id,
      ...params,
      agentIds: [],
      createdAt: new Date(),
    };

    const agentId = `agent_${params.domain}_specialist`;
    this.agentFactory.registerAgent({
      id: agentId,
      layer: 'vertical',
      visibility: 'public',
      domain: params.domain,
      description: `Especialista em ${params.name}: ${params.knowledgeAreas.join(', ')}`,
      tools: params.tools,
    });
    specialty.agentIds.push(agentId);

    this.specialties.set(id, specialty);
    this.logger.info(`[SpecialtyManager] Especialidade registrada: ${params.name} (${params.domain})`);
    return specialty;
  }

  getSpecialty(domain: string): Specialty | undefined {
    return this.specialties.get(`spec_${domain}`);
  }

  getAllSpecialties(): Specialty[] {
    return Array.from(this.specialties.values());
  }
}
