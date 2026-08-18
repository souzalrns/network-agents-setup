import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SecurityManager } from '../security/SecurityManager';

// P-028 a P-032: Governança de Dados — registro de ativos de dados com
// verificação de poisoning, "observar antes de perguntar", soberania de
// dados, regras de qualidade/validação, catálogo e linhagem.

export interface DataAsset {
  id: string;
  name: string;
  domain: string;
  classification: 'public' | 'internal' | 'confidential' | 'restricted';
  location: string; // região/jurisdição de armazenamento
  qualityScore: number; // 0-100
  lineage: string[]; // ids de ativos de origem
  registeredAt: Date;
  metadata: Record<string, any>;
}

export interface DataQualityRule {
  id: string;
  name: string;
  field: string;
  rule: 'required' | 'unique' | 'format' | 'range';
  params?: Record<string, any>;
}

export class DataGovernance extends EventEmitter {
  private assets: Map<string, DataAsset> = new Map();
  private qualityRules: DataQualityRule[] = [];
  private logger = getGlobalLogger();

  constructor(
    private securityManager: SecurityManager,
    private config: { allowedRegions?: string[] } = {}
  ) {
    super();
    this.config.allowedRegions = config.allowedRegions || ['br', 'us', 'eu'];
  }

  /**
   * Registra um novo ativo de dados, verificando poisoning antes de aceitar.
   */
  registerAsset(params: {
    name: string;
    domain: string;
    classification: DataAsset['classification'];
    location: string;
    sampleContent?: any;
    lineage?: string[];
    metadata?: Record<string, any>;
  }): DataAsset {
    if (params.sampleContent !== undefined) {
      const check = this.securityManager.detectDataPoisoning(params.sampleContent);
      if (!check.safe) {
        this.logger.warn(`[DataGovernance] Registro de ativo bloqueado por poisoning: ${check.reason}`);
        throw new Error(`Ativo de dados rejeitado: ${check.reason}`);
      }
    }

    const sovereignty = this.checkDataSovereignty(params.location);
    if (!sovereignty.allowed) {
      throw new Error(`Ativo de dados rejeitado por soberania de dados: ${sovereignty.reason}`);
    }

    const asset: DataAsset = {
      id: `data_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: params.name,
      domain: params.domain,
      classification: params.classification,
      location: params.location,
      qualityScore: 70,
      lineage: params.lineage || [],
      registeredAt: new Date(),
      metadata: params.metadata || {},
    };
    this.assets.set(asset.id, asset);
    this.logger.info(`[DataGovernance] Ativo de dados registrado: ${asset.id} - ${asset.name}`);
    this.emit('asset:registered', asset);
    return asset;
  }

  /**
   * P-030: "Observar antes de perguntar" — antes de solicitar dados ao
   * usuário, verifica se já existe um ativo equivalente registrado.
   */
  observeBeforeAsk(domain: string, name: string): DataAsset | undefined {
    const existing = Array.from(this.assets.values()).find(
      (a) => a.domain === domain && a.name.toLowerCase() === name.toLowerCase()
    );
    if (existing) {
      this.logger.info(`[DataGovernance] Dado já observado, evitando pergunta redundante: ${name}`);
    }
    return existing;
  }

  checkDataSovereignty(location: string): { allowed: boolean; reason: string } {
    const allowed = this.config.allowedRegions || ['br', 'us', 'eu'];
    if (!allowed.includes(location.toLowerCase())) {
      return { allowed: false, reason: `Região "${location}" fora das jurisdições permitidas (${allowed.join(', ')})` };
    }
    return { allowed: true, reason: 'Dentro das jurisdições permitidas' };
  }

  addQualityRule(rule: Omit<DataQualityRule, 'id'>): DataQualityRule {
    const fullRule: DataQualityRule = { id: `rule_${Date.now()}`, ...rule };
    this.qualityRules.push(fullRule);
    return fullRule;
  }

  validateQuality(assetId: string, sampleRecord: Record<string, any>): {
    valid: boolean;
    violations: string[];
  } {
    const violations: string[] = [];
    for (const rule of this.qualityRules) {
      const value = sampleRecord[rule.field];
      if (rule.rule === 'required' && (value === undefined || value === null || value === '')) {
        violations.push(`Campo obrigatório ausente: ${rule.field}`);
      }
      if (rule.rule === 'format' && rule.params?.regex && typeof value === 'string') {
        if (!new RegExp(rule.params.regex).test(value)) {
          violations.push(`Formato inválido para ${rule.field}`);
        }
      }
      if (rule.rule === 'range' && typeof value === 'number') {
        if ((rule.params?.min !== undefined && value < rule.params.min) ||
            (rule.params?.max !== undefined && value > rule.params.max)) {
          violations.push(`Valor fora do intervalo permitido para ${rule.field}`);
        }
      }
    }

    const asset = this.assets.get(assetId);
    if (asset) {
      asset.qualityScore = Math.max(0, 100 - violations.length * 15);
      this.assets.set(assetId, asset);
    }

    return { valid: violations.length === 0, violations };
  }

  getLineage(assetId: string): string[] {
    const asset = this.assets.get(assetId);
    return asset?.lineage || [];
  }

  getCatalog(domain?: string): DataAsset[] {
    const all = Array.from(this.assets.values());
    return domain ? all.filter((a) => a.domain === domain) : all;
  }

  /**
   * Lista todos os ativos de dados registrados. Método público exigido
   * pelo ComplianceManager (checkCompliance) para varrer os ativos em
   * busca de dados pessoais sujeitos à LGPD/GDPR.
   */
  listAssets(): DataAsset[] {
    return Array.from(this.assets.values());
  }

  getAsset(id: string): DataAsset | undefined {
    return this.assets.get(id);
  }
}
