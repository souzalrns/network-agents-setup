export enum DeliberationLevel {
  OPERATIONAL = 'operational',
  TACTICAL = 'tactical',
  STRATEGIC = 'strategic',
  CONSTITUTIONAL = 'constitutional',
}
export interface DeliberationCriteria {
  impact: number; // 1-10
  uncertainty: number; // 1-10
  risk: number; // 1-10
  reversibility: number; // 1-10 (quanto maior, mais reversível)
  cost: number; // 1-10
  dependencies: number; // quantidade de dependências
}
export interface DeliberationContext {
  intent: string;
  domain: string;
  criteria: DeliberationCriteria;
  previousDecisions?: string[];
  availableEvidence?: string[];
}
export interface DeliberationResult {
  level: DeliberationLevel;
  requiresApproval: boolean;
  approvalScope: 'none' | 'human' | 'council' | 'constitutional';
  confidence: number;
  suggestedAction: string;
  alternatives: string[];
  reasoning: string;
}
export class DeliberationEngine {
  constructor(private config: {
    operationalThreshold?: number;
    tacticalThreshold?: number;
    strategicThreshold?: number;
  } = {}) {
    this.config.operationalThreshold = config.operationalThreshold || 20;
    this.config.tacticalThreshold = config.tacticalThreshold || 50;
    this.config.strategicThreshold = config.strategicThreshold || 75;
  }
  /**
   * Avalia o nível de deliberação necessário
   */
  assessLevel(context: DeliberationContext): DeliberationResult {
    const score = this.calculateScore(context.criteria);
    let level: DeliberationLevel;
    let requiresApproval = false;
    let approvalScope: 'none' | 'human' | 'council' | 'constitutional' = 'none';
    let confidence = 0;
    if (score <= this.config.operationalThreshold!) {
      level = DeliberationLevel.OPERATIONAL;
      requiresApproval = false;
      approvalScope = 'none';
      confidence = 90;
    } else if (score <= this.config.tacticalThreshold!) {
      level = DeliberationLevel.TACTICAL;
      requiresApproval = true;
      approvalScope = 'human';
      confidence = 80;
    } else if (score <= this.config.strategicThreshold!) {
      level = DeliberationLevel.STRATEGIC;
      requiresApproval = true;
      approvalScope = 'council';
      confidence = 70;
    } else {
      level = DeliberationLevel.CONSTITUTIONAL;
      requiresApproval = true;
      approvalScope = 'constitutional';
      confidence = 60;
    }
    return {
      level,
      requiresApproval,
      approvalScope,
      confidence,
      suggestedAction: this.suggestAction(level),
      alternatives: this.generateAlternatives(context),
      reasoning: this.generateReasoning(level, context),
    };
  }
  /**
   * Calcula score de criticidade
   */
  private calculateScore(criteria: DeliberationCriteria): number {
    const weights = {
      impact: 0.30,
      uncertainty: 0.20,
      risk: 0.20,
      reversibility: 0.10,
      cost: 0.10,
      dependencies: 0.10,
    };
    // Ajusta reversibilidade (quanto maior, menor o score)
    const adjustedReversibility = 10 - criteria.reversibility;
    const score =
      criteria.impact * weights.impact +
      criteria.uncertainty * weights.uncertainty +
      criteria.risk * weights.risk +
      adjustedReversibility * weights.reversibility +
      criteria.cost * weights.cost +
      Math.min(criteria.dependencies, 10) * weights.dependencies;
    return Math.min(score, 100);
  }
  /**
   * Sugere ação para o nível de deliberação
   */
  private suggestAction(level: DeliberationLevel): string {
    switch (level) {
      case DeliberationLevel.OPERATIONAL:
        return 'Execute automaticamente. Não requer aprovação.';
      case DeliberationLevel.TACTICAL:
        return 'Execute após aprovação humana.';
      case DeliberationLevel.STRATEGIC:
        return 'Apresente ao Conselho de Arquitetura para avaliação.';
      case DeliberationLevel.CONSTITUTIONAL:
        return 'Submeta ao processo formal de reforma constitucional.';
      default:
        return 'Requere análise adicional.';
    }
  }
  /**
   * Gera alternativas para a deliberação
   */
  private generateAlternatives(context: DeliberationContext): string[] {
    const alternatives: string[] = [];
    // Alternativa 1: Execução direta (operacional)
    alternatives.push('Executar diretamente com recursos mínimos');
    // Alternativa 2: Execução com supervisão
    alternatives.push('Executar com supervisão humana');
    // Alternativa 3: Postergar
    alternatives.push('Adiar a decisão até mais evidências estarem disponíveis');
    // Alternativa 4: Buscar solução externa
    alternatives.push('Buscar solução existente no catálogo de capacidades');
    return alternatives;
  }
  /**
   * Gera raciocínio para a deliberação
   */
  private generateReasoning(level: DeliberationLevel, context: DeliberationContext): string {
    const criteria = context.criteria;
    const score = this.calculateScore(criteria);
    let reasoning = `Score de criticidade: ${score.toFixed(1)}/100. `;
    if (level === DeliberationLevel.OPERATIONAL) {
      reasoning += 'Baixo impacto, riscos controlados e baixo custo. Pode ser executado automaticamente.';
    } else if (level === DeliberationLevel.TACTICAL) {
      reasoning += 'Impacto moderado e riscos médios. Requer supervisão humana.';
    } else if (level === DeliberationLevel.STRATEGIC) {
      reasoning += 'Alto impacto e riscos significativos. Requer análise do Conselho de Arquitetura.';
    } else {
      reasoning += 'Impacto estrutural na Constituição. Requer processo formal de reforma.';
    }
    return reasoning;
  }
  /**
   * Escalada inteligente - decide para onde a deliberação deve ir
   */
  escalate(context: DeliberationContext): {
    target: 'none' | 'human' | 'council' | 'constitutional';
    reason: string;
    urgency: 'low' | 'medium' | 'high' | 'critical';
  } {
    const result = this.assessLevel(context);
    const urgencyMap: Record<string, 'low' | 'medium' | 'high' | 'critical'> = {
      operational: 'low',
      tactical: 'medium',
      strategic: 'high',
      constitutional: 'critical',
    };
    return {
      target: result.approvalScope,
      reason: result.reasoning,
      urgency: urgencyMap[result.level],
    };
  }
}
