import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-017: Repositório Cognitivo — armazenamento permanente de ativos de
// conhecimento com relacionamentos (dependsOn/relatedTo/supersedes) e
// pontuação de reusabilidade.

export interface KnowledgeAsset {
  id: string;
  title: string;
  type: 'fact' | 'procedure' | 'heuristic' | 'template' | 'reference';
  domain: string;
  content: any;
  tags: string[];
  reusabilityScore: number; // 0-100
  usageCount: number;
  createdAt: Date;
  updatedAt: Date;
}

export type RelationshipType = 'dependsOn' | 'relatedTo' | 'supersedes';

export interface AssetRelationship {
  fromId: string;
  toId: string;
  type: RelationshipType;
}

export class CognitiveRepository extends EventEmitter {
  private assets: Map<string, KnowledgeAsset> = new Map();
  private relationships: AssetRelationship[] = [];
  private logger = getGlobalLogger();

  registerAsset(params: {
    title: string;
    type: KnowledgeAsset['type'];
    domain: string;
    content: any;
    tags?: string[];
  }): KnowledgeAsset {
    const asset: KnowledgeAsset = {
      id: `asset_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      title: params.title,
      type: params.type,
      domain: params.domain,
      content: params.content,
      tags: params.tags || [],
      reusabilityScore: 50,
      usageCount: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.assets.set(asset.id, asset);
    this.logger.info(`[CognitiveRepository] Ativo de conhecimento registrado: ${asset.id} - ${asset.title}`);
    this.emit('asset:registered', asset);
    return asset;
  }

  relate(fromId: string, toId: string, type: RelationshipType): void {
    if (!this.assets.has(fromId) || !this.assets.has(toId)) {
      throw new Error('Ambos os ativos devem existir para relacioná-los');
    }
    this.relationships.push({ fromId, toId, type });
    this.logger.info(`[CognitiveRepository] Relacionamento criado: ${fromId} --${type}--> ${toId}`);
    this.emit('relationship:created', { fromId, toId, type });
  }

  getRelationships(assetId: string): AssetRelationship[] {
    return this.relationships.filter((r) => r.fromId === assetId || r.toId === assetId);
  }

  /**
   * Registra uso de um ativo, incrementando seu score de reusabilidade.
   */
  recordUsage(assetId: string): KnowledgeAsset {
    const asset = this.assets.get(assetId);
    if (!asset) throw new Error(`Ativo ${assetId} não encontrado`);
    asset.usageCount += 1;
    asset.reusabilityScore = Math.min(100, asset.reusabilityScore + 2);
    asset.updatedAt = new Date();
    this.assets.set(assetId, asset);
    this.emit('asset:used', asset);
    return asset;
  }

  search(query: { domain?: string; type?: KnowledgeAsset['type']; tags?: string[]; text?: string }): KnowledgeAsset[] {
    return Array.from(this.assets.values()).filter((a) => {
      if (query.domain && a.domain !== query.domain) return false;
      if (query.type && a.type !== query.type) return false;
      if (query.tags && !query.tags.some((t) => a.tags.includes(t))) return false;
      if (query.text && !a.title.toLowerCase().includes(query.text.toLowerCase())) return false;
      return true;
    });
  }

  getMostReusable(limit: number = 10): KnowledgeAsset[] {
    return Array.from(this.assets.values())
      .sort((a, b) => b.reusabilityScore - a.reusabilityScore)
      .slice(0, limit);
  }

  getAsset(id: string): KnowledgeAsset | undefined {
    return this.assets.get(id);
  }

  getAllAssets(): KnowledgeAsset[] {
    return Array.from(this.assets.values());
  }
}
