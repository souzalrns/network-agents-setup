import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { CognitiveRepository } from '../knowledge/CognitiveRepository';
import { VersionManager } from '../evolution/VersionManager';
import { AgentFactory } from '../agents/AgentFactory';
import { TokenEconomy } from '../economy/TokenEconomy';

export interface Specialty {
  id: string;
  name: string;
  description: string;
  domain: string;
  status: 'draft' | 'active' | 'deprecated' | 'archived';
  knowledge: {
    documents: string[];
    ontologies: string[];
    taxonomies: string[];
    norms: string[];
  };
  tools: string[];
  aiModels: string[];
  repositories: string[];
  skills: string[];
  mcps: string[];
  agents: string[];
  useCases: string[];
  version: string;
  createdAt: Date;
  updatedAt: Date;
  metadata: Record<string, any>;
}

export interface SpecialtyCreationRequest {
  name: string;
  description: string;
  domain: string;
  baseSpecialty?: string;
  knowledge?: Partial<Specialty['knowledge']>;
  tools?: string[];
  aiModels?: string[];
}

export class SpecialtyManager extends EventEmitter {
  private logger = getGlobalLogger();
  private specialties: Map<string, Specialty> = new Map();

  constructor(
    private cognitiveRepository: CognitiveRepository,
    private versionManager: VersionManager,
    private agentFactory: AgentFactory,
    _tokenEconomy: TokenEconomy
  ) {
    super();
    this.logger.info('[SpecialtyManager] Initialized');
    this.initializeDefaultSpecialties();
  }

  /**
   * Inicializa especialidades padrão (P-058)
   */
  private initializeDefaultSpecialties(): void {
    const specialties = [
      {
        name: 'Jurídico',
        domain: 'legal',
        description: 'Especialidade para direito com suporte a múltiplas jurisdições (BR/PT)',
        knowledge: {
          documents: ['Código Civil', 'Código de Processo Civil', 'Legislação trabalhista'],
          ontologies: ['direito_br', 'direito_pt'],
          taxonomies: ['civil', 'processual', 'trabalhista', 'tributário', 'penal'],
          norms: ['ABNT', 'ISO 27001'],
        },
        tools: ['OCR', 'Document Parser', 'Legal Research'],
        aiModels: ['gpt-4-turbo', 'claude-3-sonnet'],
        repositories: ['legal-docs-br', 'legal-docs-pt'],
        skills: ['legal-research', 'legal-drafting', 'compliance-check'],
        mcps: ['legal-mcp'],
        agents: ['legal-orchestrator', 'civil-law-br', 'civil-law-pt'],
        useCases: ['Análise de contratos', 'Pareceres jurídicos', 'Petições'],
        metadata: { priority: 'high' },
      },
      {
        name: 'HVAC',
        domain: 'hvac',
        description: 'Especialidade para refrigeração, climatização e sistemas HVAC',
        knowledge: {
          documents: ['Normas ASHRAE', 'PMOC', 'Manual de Refrigeração'],
          ontologies: ['hvac_ontology'],
          taxonomies: ['refrigeração', 'climatização', 'ventilação'],
          norms: ['ASHRAE', 'EN 378', 'ISO 5149'],
        },
        tools: ['Mollier Diagram', 'Load Calculator', 'Energy Simulator'],
        aiModels: ['gpt-4-turbo'],
        repositories: ['hvac-tools', 'refrigeration-calculator'],
        skills: ['hvac-design', 'load-calculation', 'energy-efficiency'],
        mcps: ['hvac-mcp'],
        agents: ['hvac-orchestrator', 'refrigeration-specialist', 'energy-analyst'],
        useCases: ['Dimensionamento de sistemas', 'Eficiência energética', 'Manutenção preditiva'],
        metadata: { priority: 'high' },
      },
      {
        name: 'Construção',
        domain: 'construction',
        description: 'Especialidade para construção civil, reformas e obras',
        knowledge: {
          documents: ['NBR 9050', 'NR-18', 'Manual de Obras'],
          ontologies: ['construction_ontology'],
          taxonomies: ['estrutural', 'elétrica', 'hidráulica', 'acabamentos'],
          norms: ['NBR', 'NR-10', 'NR-18'],
        },
        tools: ['BIM Viewer', 'Project Scheduler', 'Cost Estimator'],
        aiModels: ['gpt-4-turbo'],
        repositories: ['construction-bim', 'project-templates'],
        skills: ['project-planning', 'cost-estimation', 'quality-control'],
        mcps: ['construction-mcp'],
        agents: ['construction-orchestrator', 'architect-agent', 'civil-engineer'],
        useCases: ['Planejamento de obras', 'Orçamento', 'Fiscalização'],
        metadata: { priority: 'high' },
      },
      {
        name: 'Marketing',
        domain: 'marketing',
        description: 'Especialidade para marketing, publicidade e posicionamento digital',
        knowledge: {
          documents: ['Guia de SEO', 'Estratégias de Conteúdo', 'Métricas de Marketing'],
          ontologies: ['marketing_ontology'],
          taxonomies: ['conteúdo', 'mídia', 'performance', 'branding'],
          norms: ['LGPD', 'GDPR'],
        },
        tools: ['SEO Analyzer', 'Content Generator', 'Social Media Scheduler'],
        aiModels: ['gpt-4-turbo', 'claude-3-opus'],
        repositories: ['seo-tools', 'content-templates'],
        skills: ['seo-optimization', 'content-creation', 'social-media'],
        mcps: ['marketing-mcp'],
        agents: ['marketing-orchestrator', 'copywriter-agent', 'geo-agent'],
        useCases: ['Campanhas publicitárias', 'Estratégia de conteúdo', 'Posicionamento em IA'],
        metadata: { priority: 'high' },
      },
      {
        name: 'Medicina',
        domain: 'medical',
        description: 'Especialidade para medicina, hospitais e saúde (parte clínica)',
        knowledge: {
          documents: ['Protocolos Clínicos', 'CID-10', 'SNOMED CT'],
          ontologies: ['medical_ontology'],
          taxonomies: ['cardiologia', 'neurologia', 'pediatria', 'oncologia'],
          norms: ['RDC 36', 'ISO 13485'],
        },
        tools: ['Clinical Decision Support', 'Medical Image Analyzer'],
        aiModels: ['gpt-4-turbo', 'claude-3-opus'],
        repositories: ['clinical-guidelines', 'medical-datasets'],
        skills: ['clinical-diagnosis', 'medical-research', 'patient-monitoring'],
        mcps: ['medical-mcp'],
        agents: ['clinical-orchestrator', 'triage-agent', 'cardiologist-agent'],
        useCases: ['Apoio ao diagnóstico', 'Protocolos clínicos', 'Monitoramento de pacientes'],
        metadata: { priority: 'high' },
      },
    ];

    for (const spec of specialties) {
      this.createSpecialty({
        name: spec.name,
        description: spec.description,
        domain: spec.domain,
        knowledge: spec.knowledge,
        tools: spec.tools,
        aiModels: spec.aiModels,
      });
    }

    this.logger.info('[SpecialtyManager] Default specialties initialized');
  }

  /**
   * Cria uma nova especialidade (P-059, P-060)
   */
  createSpecialty(request: SpecialtyCreationRequest): Specialty {
    const id = `spec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const specialty: Specialty = {
      id,
      name: request.name,
      description: request.description,
      domain: request.domain,
      status: 'draft',
      knowledge: {
        documents: request.knowledge?.documents || [],
        ontologies: request.knowledge?.ontologies || [],
        taxonomies: request.knowledge?.taxonomies || [],
        norms: request.knowledge?.norms || [],
      },
      tools: request.tools || [],
      aiModels: request.aiModels || [],
      repositories: [],
      skills: [],
      mcps: [],
      agents: [],
      useCases: [],
      version: '1.0.0',
      createdAt: new Date(),
      updatedAt: new Date(),
      metadata: {
        createdFrom: request.baseSpecialty || 'new',
        priority: 'medium',
      },
    };

    // Se baseado em especialidade existente (P-060)
    if (request.baseSpecialty) {
      const base = this.specialties.get(request.baseSpecialty);
      if (base) {
        specialty.knowledge = {
          ...base.knowledge,
          ...request.knowledge,
        };
        specialty.tools = [...base.tools, ...(request.tools || [])];
        specialty.aiModels = [...base.aiModels, ...(request.aiModels || [])];
        specialty.metadata.createdFrom = request.baseSpecialty;
      }
    }

    this.specialties.set(id, specialty);

    // Cria versão no version manager (P-059)
    this.versionManager.createVersion(
      id,
      specialty.name,
      'ontology',
      specialty.knowledge,
      'system',
      [`Especialidade ${specialty.name} criada`],
      { domain: specialty.domain }
    );

    // Armazena no repositório cognitivo (P-059)
    this.cognitiveRepository.storeAsset({
      name: `Especialidade: ${specialty.name}`,
      type: 'capability',
      content: specialty,
      metadata: {
        author: 'system',
        tags: [specialty.domain, 'specialty'],
        domain: specialty.domain,
        confidence: 70,
        validationStatus: 'pending',
        source: 'SpecialtyManager',
      },
    });

    this.logger.info(`[SpecialtyManager] Specialty created: ${id}`);
    this.emit('specialty:created', specialty);

    return specialty;
  }

  /**
   * Ativa uma especialidade (torna disponível)
   */
  activateSpecialty(specialtyId: string): Specialty {
    const specialty = this.specialties.get(specialtyId);
    if (!specialty) {
      throw new Error(`Specialty ${specialtyId} not found`);
    }

    specialty.status = 'active';
    specialty.updatedAt = new Date();
    this.specialties.set(specialtyId, specialty);

    // Cria agentes para a especialidade (P-059)
    this.createSpecialtyAgents(specialty);

    this.logger.info(`[SpecialtyManager] Specialty activated: ${specialtyId}`);
    this.emit('specialty:activated', specialty);

    return specialty;
  }

  /**
   * Cria agentes para uma especialidade (P-059)
   */
  private createSpecialtyAgents(specialty: Specialty): void {
    // Cria agente orquestrador da especialidade
    const orchestratorId = `${specialty.domain}-orchestrator`;
    this.agentFactory.registerAgent({
      id: orchestratorId,
      layer: 'vertical',
      visibility: 'private',
      domain: specialty.domain,
      description: `Orquestrador para especialidade ${specialty.name}`,
      systemPrompt: `Você é um orquestrador especializado em ${specialty.name}. Coordene os agentes da especialidade.`,
      tools: specialty.tools,
    });

    // Cria agentes especialistas baseados nos casos de uso
    for (const useCase of specialty.useCases.slice(0, 3)) {
      const agentId = `${specialty.domain}-${useCase.replace(/\s+/g, '-').toLowerCase()}`;
      this.agentFactory.registerAgent({
        id: agentId,
        layer: 'vertical',
        visibility: 'private',
        domain: specialty.domain,
        description: `Especialista em ${useCase} para ${specialty.name}`,
        systemPrompt: `Você é um especialista em ${useCase} para ${specialty.name}.`,
        tools: specialty.tools,
      });
    }

    this.logger.info(`[SpecialtyManager] Agents created for specialty: ${specialty.id}`);
  }

  /**
   * Define conhecimento/normas/ferramentas para uma especialidade (P-059)
   */
  defineSpecialtyKnowledge(
    specialtyId: string,
    knowledge: Partial<Specialty['knowledge']>
  ): Specialty {
    const specialty = this.specialties.get(specialtyId);
    if (!specialty) {
      throw new Error(`Specialty ${specialtyId} not found`);
    }

    specialty.knowledge = {
      ...specialty.knowledge,
      ...knowledge,
    };
    specialty.updatedAt = new Date();

    // Atualiza versão
    this.versionManager.createVersion(
      specialtyId,
      specialty.name,
      'ontology',
      specialty.knowledge,
      'system',
      ['Conhecimento atualizado'],
      { domain: specialty.domain }
    );

    this.specialties.set(specialtyId, specialty);
    this.logger.info(`[SpecialtyManager] Knowledge defined for: ${specialtyId}`);
    this.emit('specialty:knowledge_updated', specialty);

    return specialty;
  }

  /**
   * Adiciona caso de uso a uma especialidade (P-059)
   */
  addUseCase(specialtyId: string, useCase: string): Specialty {
    const specialty = this.specialties.get(specialtyId);
    if (!specialty) {
      throw new Error(`Specialty ${specialtyId} not found`);
    }

    if (!specialty.useCases.includes(useCase)) {
      specialty.useCases.push(useCase);
      specialty.updatedAt = new Date();
      this.specialties.set(specialtyId, specialty);

      // Cria agente para o novo caso de uso
      const agentId = `${specialty.domain}-${useCase.replace(/\s+/g, '-').toLowerCase()}`;
      this.agentFactory.registerAgent({
        id: agentId,
        layer: 'vertical',
        visibility: 'private',
        domain: specialty.domain,
        description: `Especialista em ${useCase} para ${specialty.name}`,
        systemPrompt: `Você é um especialista em ${useCase} para ${specialty.name}.`,
        tools: specialty.tools,
      });

      this.logger.info(`[SpecialtyManager] Use case added: ${useCase}`);
      this.emit('specialty:usecase_added', { specialtyId, useCase });
    }

    return specialty;
  }

  /**
   * Obtém especialidade por ID
   */
  getSpecialty(id: string): Specialty | undefined {
    return this.specialties.get(id);
  }

  /**
   * Obtém especialidades por domínio
   */
  getSpecialtiesByDomain(domain: string): Specialty[] {
    return Array.from(this.specialties.values())
      .filter((s) => s.domain === domain);
  }

  /**
   * Obtém especialidades ativas
   */
  getActiveSpecialties(): Specialty[] {
    return Array.from(this.specialties.values())
      .filter((s) => s.status === 'active');
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    total: number;
    active: number;
    draft: number;
    deprecated: number;
    archived: number;
    byDomain: Record<string, number>;
  } {
    const specialties = Array.from(this.specialties.values());
    const byDomain: Record<string, number> = {};

    for (const spec of specialties) {
      byDomain[spec.domain] = (byDomain[spec.domain] || 0) + 1;
    }

    return {
      total: specialties.length,
      active: specialties.filter((s) => s.status === 'active').length,
      draft: specialties.filter((s) => s.status === 'draft').length,
      deprecated: specialties.filter((s) => s.status === 'deprecated').length,
      archived: specialties.filter((s) => s.status === 'archived').length,
      byDomain,
    };
  }
}
