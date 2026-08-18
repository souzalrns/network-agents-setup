import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { VersionManager } from '../evolution/VersionManager';
import { SelfAwareness } from '../observability/SelfAwareness';

export interface KnowledgeAsset {
  id: string;
  name: string;
  type: 'document' | 'ontology' | 'model' | 'decision' | 'experience' | 'capability';
  content: any;
  metadata: {
    author: string;
    createdAt: Date;
    updatedAt: Date;
    tags: string[];
    domain: string;
    confidence: number; // 0-100
    validationStatus: 'pending' | 'validated' | 'invalidated';
    source: string;
    version: string;
    reusability: number; // 0-100
  };
  relationships: {
    dependsOn: string[];
    relatedTo: string[];
    supersedes?: string;
    supersededBy?: string;
  };
}

// Nota de fidelidade: no material original, `storeAsset` omitia o campo
// `metadata` por completo do tipo de entrada (Omit<KnowledgeAsset, 'id' |
// 'metadata' | 'relationships'>), mas o próprio corpo do método lia
// `asset.metadata.author`, `.tags`, `.domain`, etc. — um erro de compilação
// real, já que quem chamava sempre passava um `metadata` parcial (ver
// HorizontalAgents, SpecialtyManager, ProductManager, DocumentationGovernance
// e AIVisibilityEngine... na verdade os módulos que chamam storeAsset).
// Corrigido para exigir apenas os subcampos de metadata que o método
// efetivamente usa como entrada, deixando os demais (createdAt, updatedAt,
// version, reusability) como calculados internamente.
export type StoreAssetInput = Omit<KnowledgeAsset, 'id' | 'relationships' | 'metadata'> & {
  metadata: Partial<Pick<KnowledgeAsset['metadata'], 'author' | 'tags' | 'domain' | 'confidence' | 'validationStatus' | 'source'>>;
};

export class CognitiveRepository extends EventEmitter {
  private logger = getGlobalLogger();
  private assets: Map<string, KnowledgeAsset> = new Map();

  constructor(
    private versionManager: VersionManager,
    _selfAwareness: SelfAwareness
  ) {
    super();
    this.logger.info('[CognitiveRepository] Initialized');
  }

  /**
   * Armazena um ativo de conhecimento (P-017)
   */
  storeAsset(asset: StoreAssetInput): KnowledgeAsset {
    const id = `asset_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const fullAsset: KnowledgeAsset = {
      ...asset,
      id,
      metadata: {
        author: asset.metadata.author || 'system',
        createdAt: new Date(),
        updatedAt: new Date(),
        tags: asset.metadata.tags || [],
        domain: asset.metadata.domain || 'general',
        confidence: asset.metadata.confidence || 50,
        validationStatus: asset.metadata.validationStatus || 'pending',
        source: asset.metadata.source || 'unknown',
        version: '1.0.0',
        reusability: 0,
      },
      relationships: {
        dependsOn: [],
        relatedTo: [],
      },
    };

    this.assets.set(id, fullAsset);

    // Cria versão no version manager
    this.versionManager.createVersion(
      id,
      asset.name,
      'knowledge',
      asset.content,
      asset.metadata.author || 'system',
      ['Asset created'],
      { type: asset.type, domain: asset.metadata.domain }
    );

    this.logger.info(`[CognitiveRepository] Asset stored: ${id} - ${asset.name}`);
    this.emit('asset:stored', fullAsset);

    return fullAsset;
  }

  /**
   * Atualiza um ativo de conhecimento
   */
  updateAsset(id: string, updates: Partial<KnowledgeAsset>): KnowledgeAsset {
    const asset = this.assets.get(id);
    if (!asset) {
      throw new Error(`Asset ${id} not found`);
    }

    const updated = { ...asset, ...updates };
    updated.metadata.updatedAt = new Date();

    // Cria nova versão
    this.versionManager.createVersion(
      id,
      updated.name,
      'knowledge',
      updated.content,
      'system',
      ['Asset updated'],
      { type: updated.type }
    );

    this.assets.set(id, updated);
    this.logger.info(`[CognitiveRepository] Asset updated: ${id}`);
    this.emit('asset:updated', updated);

    return updated;
  }

  /**
   * Busca ativos por domínio
   */
  findAssets(domain: string): KnowledgeAsset[] {
    return Array.from(this.assets.values()).filter(
      (a) => a.metadata.domain === domain
    );
  }

  /**
   * Busca ativos por tags
   */
  findAssetsByTags(tags: string[]): KnowledgeAsset[] {
    return Array.from(this.assets.values()).filter(
      (a) => tags.some((tag) => a.metadata.tags.includes(tag))
    );
  }

  /**
   * Busca ativos por tipo
   */
  findAssetsByType(type: KnowledgeAsset['type']): KnowledgeAsset[] {
    return Array.from(this.assets.values()).filter(
      (a) => a.type === type
    );
  }

  /**
   * Busca ativos reutilizáveis
   */
  findReusableAssets(minReusability: number = 70): KnowledgeAsset[] {
    return Array.from(this.assets.values()).filter(
      (a) => a.metadata.reusability >= minReusability
    );
  }

  /**
   * Atualiza reusabilidade de um ativo
   */
  updateReusability(id: string): void {
    const asset = this.assets.get(id);
    if (!asset) {
      throw new Error(`Asset ${id} not found`);
    }

    // Calcula reusabilidade baseada em uso e confiança
    const confidence = asset.metadata.confidence;
    const validation = asset.metadata.validationStatus === 'validated' ? 20 : 0;
    const age = (Date.now() - asset.metadata.createdAt.getTime()) / (1000 * 60 * 60 * 24);
    const ageBonus = Math.min(age / 30, 20);

    asset.metadata.reusability = Math.min(confidence * 0.6 + validation + ageBonus, 100);
    this.assets.set(id, asset);
  }

  /**
   * Relaciona dois ativos
   */
  relateAssets(sourceId: string, targetId: string, type: 'dependsOn' | 'relatedTo' | 'supersedes'): void {
    const source = this.assets.get(sourceId);
    const target = this.assets.get(targetId);

    if (!source || !target) {
      throw new Error('Asset not found');
    }

    if (type === 'dependsOn') {
      source.relationships.dependsOn.push(targetId);
    } else if (type === 'relatedTo') {
      source.relationships.relatedTo.push(targetId);
    } else if (type === 'supersedes') {
      source.relationships.supersedes = targetId;
      target.relationships.supersededBy = sourceId;
    }

    this.assets.set(sourceId, source);
    this.assets.set(targetId, target);
  }

  /**
   * Obtém ativo por ID
   */
  getAsset(id: string): KnowledgeAsset | undefined {
    return this.assets.get(id);
  }

  /**
   * Lista todos os ativos
   */
  listAssets(): KnowledgeAsset[] {
    return Array.from(this.assets.values());
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalAssets: number;
    byType: Record<KnowledgeAsset['type'], number>;
    validated: number;
    pending: number;
    avgReusability: number;
  } {
    const assets = Array.from(this.assets.values());
    const types: Record<string, number> = {};

    for (const asset of assets) {
      types[asset.type] = (types[asset.type] || 0) + 1;
    }

    const validated = assets.filter((a) => a.metadata.validationStatus === 'validated').length;
    const pending = assets.filter((a) => a.metadata.validationStatus === 'pending').length;
    const avgReusability = assets.reduce((sum, a) => sum + a.metadata.reusability, 0) / (assets.length || 1);

    return {
      totalAssets: assets.length,
      byType: types as Record<KnowledgeAsset['type'], number>,
      validated,
      pending,
      avgReusability,
    };
  }
}
