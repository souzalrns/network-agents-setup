import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SecurityManager } from '../security/SecurityManager';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';

export interface DataAsset {
  id: string;
  name: string;
  type: 'structured' | 'semi-structured' | 'unstructured';
  source: string;
  format: string;
  size: number;
  createdAt: Date;
  updatedAt: Date;
  owner: string;
  classification: 'public' | 'internal' | 'restricted' | 'confidential' | 'critical';
  retentionDays: number;
  tags: string[];
  lineage: {
    source: string;
    transformations: string[];
    derivedFrom?: string[];
  };
  quality: {
    completeness: number; // 0-100
    accuracy: number; // 0-100
    consistency: number; // 0-100
    timeliness: number; // 0-100
    overall: number; // 0-100
  };
  metadata: Record<string, any>;
}

export interface DataQualityRule {
  id: string;
  name: string;
  description: string;
  type: 'completeness' | 'accuracy' | 'consistency' | 'timeliness' | 'uniqueness' | 'validity';
  threshold: number;
  appliesTo: string[];
  action: 'warn' | 'block' | 'fix';
}

export class DataGovernance extends EventEmitter {
  private logger = getGlobalLogger();
  private assets: Map<string, DataAsset> = new Map();
  private qualityRules: Map<string, DataQualityRule> = new Map();

  constructor(
    private securityManager: SecurityManager,
    _immunologicalMemory: ImmunologicalMemory
  ) {
    super();
    this.logger.info('[DataGovernance] Initialized');
  }

  // ===== P-028: Ingestão Universal de Dados =====

  /**
   * Registra um novo ativo de dados
   */
  registerDataAsset(data: Omit<DataAsset, 'id' | 'createdAt' | 'updatedAt' | 'quality'>): DataAsset {
    const id = `data_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    // Verifica segurança
    const securityCheck = this.securityManager.detectDataPoisoning(data);
    if (!securityCheck.safe) {
      throw new Error(`Data rejected: ${securityCheck.reason}`);
    }

    const asset: DataAsset = {
      ...data,
      id,
      createdAt: new Date(),
      updatedAt: new Date(),
      quality: {
        completeness: 100,
        accuracy: 100,
        consistency: 100,
        timeliness: 100,
        overall: 100,
      },
    };

    this.assets.set(id, asset);
    this.logger.info(`[DataGovernance] Data asset registered: ${id}`);
    this.emit('data:registered', asset);

    return asset;
  }

  // ===== P-029: Observação antes da Pergunta =====

  /**
   * Observa dados automaticamente
   */
  async observeData(source: string): Promise<DataAsset[]> {
    this.logger.info(`[DataGovernance] Observing data from: ${source}`);

    // Simula observação de dados
    // Em produção, isso se conectaria a sensores, APIs, etc.
    const observed: DataAsset[] = [];

    // Verifica se já existe
    const existing = Array.from(this.assets.values()).filter(
      (a) => a.source === source
    );

    if (existing.length > 0) {
      this.logger.info(`[DataGovernance] Found ${existing.length} existing assets from ${source}`);
      return existing;
    }

    // Cria observação
    const asset = this.registerDataAsset({
      name: `Data from ${source}`,
      type: 'unstructured',
      source,
      format: 'raw',
      size: 0,
      owner: 'system',
      classification: 'internal',
      retentionDays: 365,
      tags: ['observed'],
      lineage: {
        source,
        transformations: [],
      },
      metadata: {
        observedAt: new Date(),
        observedBy: 'DataGovernance',
      },
    });

    observed.push(asset);

    this.emit('data:observed', observed);
    return observed;
  }

  // ===== P-030: Soberania dos Dados =====

  /**
   * Verifica soberania dos dados
   */
  checkDataSovereignty(dataId: string, context: { userId?: string; organization?: string }): {
    sovereign: boolean;
    reason: string;
    permittedActions: string[];
  } {
    const asset = this.assets.get(dataId);
    if (!asset) {
      return { sovereign: false, reason: 'Data asset not found', permittedActions: [] };
    }

    // Verifica proprietário
    if (context.userId && asset.owner !== context.userId) {
      return {
        sovereign: false,
        reason: `Data owned by ${asset.owner}, not ${context.userId}`,
        permittedActions: ['read'],
      };
    }

    // Verifica classificação
    const permitted: string[] = ['read'];
    if (asset.classification === 'public') {
      permitted.push('write', 'delete', 'share');
    } else if (asset.classification === 'internal' && context.organization) {
      permitted.push('write');
    } else if (asset.classification === 'restricted') {
      permitted.push('write');
    }

    return {
      sovereign: true,
      reason: 'Data sovereignty verified',
      permittedActions: permitted,
    };
  }

  // ===== P-031: Qualidade de Dados =====

  /**
   * Avalia qualidade de um ativo de dados
   */
  assessDataQuality(dataId: string): DataAsset['quality'] {
    const asset = this.assets.get(dataId);
    if (!asset) {
      throw new Error(`Data asset ${dataId} not found`);
    }

    // Simula avaliação de qualidade
    const quality = {
      completeness: 70 + Math.random() * 30,
      accuracy: 70 + Math.random() * 30,
      consistency: 70 + Math.random() * 30,
      timeliness: 70 + Math.random() * 30,
      overall: 0,
    };

    quality.overall = (
      quality.completeness +
      quality.accuracy +
      quality.consistency +
      quality.timeliness
    ) / 4;

    asset.quality = quality;
    this.assets.set(dataId, asset);

    this.emit('data:quality_assessed', { dataId, quality });
    return quality;
  }

  /**
   * Define regra de qualidade
   */
  defineQualityRule(rule: Omit<DataQualityRule, 'id'>): DataQualityRule {
    const id = `rule_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const fullRule: DataQualityRule = {
      ...rule,
      id,
    };

    this.qualityRules.set(id, fullRule);
    this.logger.info(`[DataGovernance] Quality rule defined: ${id}`);
    this.emit('quality:rule_defined', fullRule);

    return fullRule;
  }

  /**
   * Valida dados contra regras de qualidade
   */
  validateData(dataId: string): {
    passed: boolean;
    failures: Array<{ ruleId: string; message: string }>;
    score: number;
  } {
    const asset = this.assets.get(dataId);
    if (!asset) {
      throw new Error(`Data asset ${dataId} not found`);
    }

    const failures: Array<{ ruleId: string; message: string }> = [];
    const rules = Array.from(this.qualityRules.values());

    for (const rule of rules) {
      if (!rule.appliesTo.includes(asset.type)) continue;

      const value = asset.quality[rule.type as keyof DataAsset['quality']] || 0;
      if (typeof value === 'number' && value < rule.threshold) {
        failures.push({
          ruleId: rule.id,
          message: `Rule "${rule.name}" failed: ${value} < ${rule.threshold}`,
        });
      }
    }

    const passed = failures.length === 0;
    const score = passed ? 100 : Math.max(0, 100 - failures.length * 10);

    return { passed, failures, score };
  }

  // ===== P-032: Governança de Dados =====

  /**
   * Cria catálogo de dados
   */
  createDataCatalog(): {
    assets: DataAsset[];
    stats: {
      total: number;
      byType: Record<string, number>;
      byClassification: Record<string, number>;
    };
  } {
    const assets = Array.from(this.assets.values());
    const stats = {
      total: assets.length,
      byType: {} as Record<string, number>,
      byClassification: {} as Record<string, number>,
    };

    for (const asset of assets) {
      stats.byType[asset.type] = (stats.byType[asset.type] || 0) + 1;
      stats.byClassification[asset.classification] = (stats.byClassification[asset.classification] || 0) + 1;
    }

    return { assets, stats };
  }

  /**
   * Lista todos os ativos de dados
   *
   * Nota de fidelidade: método ausente no material original, embora
   * ComplianceManager (P-078) já chamasse `dataGovernance.listAssets()`
   * seguindo o mesmo padrão usado em CognitiveRepository.listAssets().
   * Adicionado aqui para corrigir esse erro de compilação real.
   */
  listAssets(): DataAsset[] {
    return Array.from(this.assets.values());
  }

  /**
   * Obtém linhagem de dados
   */
  getDataLineage(dataId: string): {
    asset: DataAsset;
    source: string;
    transformations: string[];
    derivedFrom?: string[];
  } {
    const asset = this.assets.get(dataId);
    if (!asset) {
      throw new Error(`Data asset ${dataId} not found`);
    }

    return {
      asset,
      source: asset.lineage.source,
      transformations: asset.lineage.transformations,
      derivedFrom: asset.lineage.derivedFrom,
    };
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalAssets: number;
    avgQuality: number;
    rules: number;
    sovereign: number;
  } {
    const assets = Array.from(this.assets.values());
    const avgQuality = assets.reduce((sum, a) => sum + a.quality.overall, 0) / (assets.length || 1);
    const sovereign = assets.filter((a) => a.classification !== 'public').length;

    return {
      totalAssets: assets.length,
      avgQuality,
      rules: this.qualityRules.size,
      sovereign,
    };
  }
}
