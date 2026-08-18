import { getGlobalLogger } from '@network-agents/observability';
import { TokenEconomy, CostOptimization } from '../economy/TokenEconomy';
import { CognitiveRepository, KnowledgeAsset } from '../knowledge/CognitiveRepository';

// P-024: Agentes Horizontais — utilitários compartilhados por todos os
// domínios verticais: otimização de prompt, sugestão de otimização de
// tokens, gestão de cache, recuperação de conhecimento, análise de
// risco, garantia de qualidade, gestão de custo e roteamento de modelo.

export class HorizontalAgents {
  private logger = getGlobalLogger();

  constructor(
    private tokenEconomy: TokenEconomy,
    private cognitiveRepository?: CognitiveRepository
  ) {}

  /**
   * Otimiza um prompt removendo redundâncias óbvias e comprimindo espaços.
   */
  optimizePrompt(prompt: string): { optimized: string; reduction: number } {
    const optimized = prompt
      .replace(/\s+/g, ' ')
      .replace(/(please|por favor)\s*,?\s*/gi, '')
      .trim();
    const reduction = prompt.length > 0 ? ((prompt.length - optimized.length) / prompt.length) * 100 : 0;
    this.logger.debug(`[HorizontalAgents] Prompt otimizado com redução de ${reduction.toFixed(1)}%`);
    return { optimized, reduction };
  }

  suggestTokenOptimizations(executionId: string): CostOptimization[] {
    return this.tokenEconomy.getOptimizations(executionId);
  }

  manageCache(action: 'clean' | 'stats', maxAgeSeconds?: number) {
    if (action === 'clean') {
      this.tokenEconomy.cleanCache(maxAgeSeconds);
      return { cleaned: true };
    }
    return this.tokenEconomy.getCacheStats();
  }

  retrieveKnowledge(query: { domain?: string; text?: string }): KnowledgeAsset[] {
    if (!this.cognitiveRepository) return [];
    return this.cognitiveRepository.search(query);
  }

  /**
   * Análise de risco simplificada baseada em palavras-chave sensíveis e
   * no tamanho/complexidade da solicitação.
   */
  analyzeRisk(input: string): { level: 'low' | 'medium' | 'high'; factors: string[] } {
    const factors: string[] = [];
    const highRiskTerms = ['financeiro', 'contrato', 'saúde', 'jurídico', 'irreversível', 'exclu'];
    for (const term of highRiskTerms) {
      if (input.toLowerCase().includes(term)) factors.push(`Termo sensível: "${term}"`);
    }
    if (input.length > 2000) factors.push('Solicitação extensa/complexa');

    const level: 'low' | 'medium' | 'high' = factors.length >= 2 ? 'high' : factors.length === 1 ? 'medium' : 'low';
    return { level, factors };
  }

  /**
   * Garantia de qualidade básica sobre uma saída gerada.
   */
  qualityAssurance(output: string): { passed: boolean; issues: string[] } {
    const issues: string[] = [];
    if (!output || output.trim().length === 0) issues.push('Saída vazia');
    if (output && output.includes('undefined')) issues.push('Possível valor não tratado ("undefined") na saída');
    if (output && output.length < 5) issues.push('Saída suspeita por ser muito curta');
    return { passed: issues.length === 0, issues };
  }

  manageCost(executionId: string): { savings: ReturnType<TokenEconomy['getSavingsMetrics']> } {
    return { savings: this.tokenEconomy.getSavingsMetrics(executionId) };
  }

  /**
   * Roteia para o modelo mais adequado com base na complexidade estimada.
   */
  routeModel(complexity: 'low' | 'medium' | 'high'): string {
    const routes: Record<string, string> = {
      low: 'gpt-3.5-turbo',
      medium: 'claude-3-sonnet',
      high: 'gpt-4-turbo',
    };
    return routes[complexity] || 'gpt-4-turbo';
  }
}
