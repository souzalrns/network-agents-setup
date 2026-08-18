import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-070 a P-074: Motor de Visibilidade para IA — rastreamento de
// visibilidade SEO/IA de ativos digitais, checklist automatizado
// (P-071), modelagem de grafo de conhecimento Schema.org (P-072),
// verificação de valor de conteúdo (P-073) e ciclo contínuo
// publicar -> indexar -> medir -> diagnosticar -> melhorar (P-074).

export interface DigitalAsset {
  id: string;
  url: string;
  title: string;
  visibilityScore: number; // 0-100
  lastChecked?: Date;
  registeredAt: Date;
}

export interface VisibilityChecklistResult {
  hasStructuredData: boolean;
  hasMetaDescription: boolean;
  hasSemanticHeadings: boolean;
  isMobileFriendly: boolean;
  loadTimeOk: boolean;
  score: number;
  issues: string[];
}

export interface SchemaGraphNode {
  '@type': string;
  [key: string]: any;
}

export class AIVisibilityEngine extends EventEmitter {
  private assets: Map<string, DigitalAsset> = new Map();
  private logger = getGlobalLogger();

  registerAsset(url: string, title: string): DigitalAsset {
    const asset: DigitalAsset = {
      id: `dasset_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      url,
      title,
      visibilityScore: 0,
      registeredAt: new Date(),
    };
    this.assets.set(asset.id, asset);
    this.logger.info(`[AIVisibilityEngine] Ativo digital registrado: ${title} (${url})`);
    this.emit('asset:registered', asset);
    return asset;
  }

  /**
   * P-071: Checklist automatizado de visibilidade para IA/SEO.
   */
  runChecklist(assetId: string, signals: {
    hasStructuredData: boolean;
    hasMetaDescription: boolean;
    hasSemanticHeadings: boolean;
    isMobileFriendly: boolean;
    loadTimeMs: number;
  }): VisibilityChecklistResult {
    const asset = this.assets.get(assetId);
    if (!asset) throw new Error(`Ativo ${assetId} não encontrado`);

    const issues: string[] = [];
    if (!signals.hasStructuredData) issues.push('Sem dados estruturados (Schema.org)');
    if (!signals.hasMetaDescription) issues.push('Sem meta description');
    if (!signals.hasSemanticHeadings) issues.push('Sem hierarquia semântica de headings');
    if (!signals.isMobileFriendly) issues.push('Não otimizado para mobile');

    const loadTimeOk = signals.loadTimeMs <= 3000;
    if (!loadTimeOk) issues.push(`Tempo de carregamento alto: ${signals.loadTimeMs}ms`);

    const checks = [
      signals.hasStructuredData,
      signals.hasMetaDescription,
      signals.hasSemanticHeadings,
      signals.isMobileFriendly,
      loadTimeOk,
    ];
    const score = (checks.filter(Boolean).length / checks.length) * 100;

    asset.visibilityScore = score;
    asset.lastChecked = new Date();
    this.assets.set(assetId, asset);

    return {
      hasStructuredData: signals.hasStructuredData,
      hasMetaDescription: signals.hasMetaDescription,
      hasSemanticHeadings: signals.hasSemanticHeadings,
      isMobileFriendly: signals.isMobileFriendly,
      loadTimeOk,
      score,
      issues,
    };
  }

  /**
   * P-072: Modela um nó de grafo de conhecimento Schema.org para o ativo.
   */
  buildSchemaGraph(assetId: string, type: string, properties: Record<string, any>): SchemaGraphNode {
    const asset = this.assets.get(assetId);
    if (!asset) throw new Error(`Ativo ${assetId} não encontrado`);
    return {
      '@context': 'https://schema.org',
      '@type': type,
      url: asset.url,
      name: asset.title,
      ...properties,
    };
  }

  /**
   * P-073: Verifica se o conteúdo agrega valor real (não apenas volume).
   */
  checkContentValue(content: string): { valuable: boolean; reasons: string[] } {
    const reasons: string[] = [];
    const wordCount = content.trim().split(/\s+/).filter(Boolean).length;
    if (wordCount < 150) reasons.push('Conteúdo muito curto para agregar valor real');
    const uniqueSentences = new Set(content.split(/[.!?]/).map((s) => s.trim().toLowerCase())).size;
    const totalSentences = content.split(/[.!?]/).filter((s) => s.trim().length > 0).length;
    if (totalSentences > 0 && uniqueSentences / totalSentences < 0.7) {
      reasons.push('Alto grau de repetição/redundância detectado');
    }
    return { valuable: reasons.length === 0, reasons };
  }

  /**
   * P-074: Executa um ciclo contínuo publicar -> indexar -> medir ->
   * diagnosticar -> melhorar para um ativo digital.
   */
  async runContinuousCycle(assetId: string): Promise<{
    stage: 'published' | 'indexed' | 'measured' | 'diagnosed' | 'improved';
    notes: string;
  }> {
    const asset = this.assets.get(assetId);
    if (!asset) throw new Error(`Ativo ${assetId} não encontrado`);

    this.emit('cycle:published', asset);
    this.emit('cycle:indexed', asset);

    const measured = asset.visibilityScore;
    this.emit('cycle:measured', { asset, score: measured });

    const diagnosis = measured < 60 ? 'Visibilidade abaixo do ideal, requer melhorias' : 'Visibilidade adequada';
    this.emit('cycle:diagnosed', { asset, diagnosis });

    if (measured < 60) {
      this.emit('cycle:improved', asset);
      return { stage: 'improved', notes: diagnosis };
    }

    return { stage: 'diagnosed', notes: diagnosis };
  }

  getAsset(id: string): DigitalAsset | undefined {
    return this.assets.get(id);
  }

  getAllAssets(): DigitalAsset[] {
    return Array.from(this.assets.values());
  }
}
