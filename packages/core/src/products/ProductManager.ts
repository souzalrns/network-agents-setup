import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SpecialtyManager } from '../domains/SpecialtyManager';
import { CognitiveRepository } from '../knowledge/CognitiveRepository';
import { TokenEconomy } from '../economy/TokenEconomy';
import { SelfAwareness } from '../observability/SelfAwareness';

export interface CognitiveProduct {
  id: string;
  name: string;
  description: string;
  specialtyId: string;
  capabilities: string[];
  status: 'development' | 'beta' | 'production' | 'deprecated';
  version: string;
  metrics: {
    users: number;
    satisfaction: number; // 0-100
    revenue: number;
    cost: number;
    roi: number;
  };
  roadmap: string[];
  createdAt: Date;
  updatedAt: Date;
  metadata: Record<string, any>;
}

export class ProductManager extends EventEmitter {
  private logger = getGlobalLogger();
  private products: Map<string, CognitiveProduct> = new Map();

  constructor(
    _specialtyManager: SpecialtyManager,
    private cognitiveRepository: CognitiveRepository,
    private tokenEconomy: TokenEconomy,
    _selfAwareness: SelfAwareness
  ) {
    super();
    this.logger.info('[ProductManager] Initialized');
    this.initializeDefaultProducts();
  }

  /**
   * Inicializa produtos padrão (P-061)
   */
  private initializeDefaultProducts(): void {
    const products = [
      {
        name: 'Coach Financeiro',
        description: 'Assistente financeiro pessoal com OCR para notas fiscais',
        specialtyId: 'financeiro',
        capabilities: ['ocr', 'financial-analysis', 'budgeting'],
        roadmap: ['Integração com bancos', 'Previsão de gastos', 'Relatórios automáticos'],
      },
      {
        name: 'Gestão de Obras',
        description: 'Sistema completo para gestão de obras e reformas',
        specialtyId: 'construction',
        capabilities: ['project-planning', 'cost-estimation', 'quality-control'],
        roadmap: ['Integração com BIM', 'Drones para inspeção', 'Realidade aumentada'],
      },
      {
        name: 'Monitoramento de Idosos',
        description: 'Sistema de monitoramento remoto para idosos com IA',
        specialtyId: 'medical',
        capabilities: ['patient-monitoring', 'fall-detection', 'alert-system'],
        roadmap: ['Wi-Fi CSI', 'Integração com smartwatches', 'IA preditiva'],
      },
      {
        name: 'Inspeção com Drones',
        description: 'Plataforma para inspeção de sinistros com drones',
        specialtyId: 'construction',
        capabilities: ['drone-control', 'image-analysis', 'report-generation'],
        roadmap: ['Reconhecimento de danos', 'Análise 3D', 'Integração com seguradoras'],
      },
      {
        name: 'Gestão de Condomínios',
        description: 'Sistema para gestão de condomínios e manutenções',
        specialtyId: 'business',
        capabilities: ['ticketing', 'inventory', 'financial'],
        roadmap: ['Portal do morador', 'Automação de manutenção', 'Licitações digitais'],
      },
      {
        name: 'Gestão Pública',
        description: 'Plataforma para gestão de demandas públicas',
        specialtyId: 'government',
        capabilities: ['ticketing', 'workflow', 'analytics'],
        roadmap: ['Integração com governos', 'Painéis de transparência', 'IA para priorização'],
      },
      {
        name: 'Sistema de Licitações',
        description: 'Sistema digital para licitações e contratações',
        specialtyId: 'legal',
        capabilities: ['document-processing', 'workflow', 'compliance'],
        roadmap: ['Integração com portais', 'Análise de propostas', 'IA para seleção'],
      },
    ];

    for (const product of products) {
      this.createProduct(product);
    }

    this.logger.info('[ProductManager] Default products initialized');
  }

  /**
   * Cria um novo produto cognitivo (P-061)
   */
  createProduct(data: {
    name: string;
    description: string;
    specialtyId: string;
    capabilities: string[];
    roadmap?: string[];
  }): CognitiveProduct {
    const id = `prod_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const product: CognitiveProduct = {
      id,
      name: data.name,
      description: data.description,
      specialtyId: data.specialtyId,
      capabilities: data.capabilities,
      status: 'development',
      version: '0.1.0',
      metrics: {
        users: 0,
        satisfaction: 0,
        revenue: 0,
        cost: 0,
        roi: 0,
      },
      roadmap: data.roadmap || [],
      createdAt: new Date(),
      updatedAt: new Date(),
      metadata: {
        createdBy: 'ProductManager',
      },
    };

    this.products.set(id, product);

    // P-062: Produto como composição de capacidades
    this.composeProductCapabilities(product);

    // P-063: Inicia ciclo de vida
    this.startProductLifecycle(product);

    this.logger.info(`[ProductManager] Product created: ${id}`);
    this.emit('product:created', product);

    return product;
  }

  /**
   * Compõe produto a partir de capacidades reutilizáveis (P-062)
   */
  private composeProductCapabilities(product: CognitiveProduct): void {
    const capabilities = product.capabilities;

    this.logger.info(`[ProductManager] Composing product ${product.id} from capabilities: ${capabilities.join(', ')}`);

    // Verifica se as capacidades existem no repositório
    const assets = this.cognitiveRepository.listAssets();
    const availableCapabilities = assets.filter((a) =>
      capabilities.some((cap) => a.metadata.tags.includes(cap))
    );

    if (availableCapabilities.length < capabilities.length) {
      this.logger.warn(
        `[ProductManager] Some capabilities missing for product ${product.id}`
      );
    }

    // P-062: Reutilização de capacidades
    capabilities.forEach(() => {
      this.tokenEconomy.recordUsage(product.id, {
        model: 'reuse',
        inputTokens: 0,
        outputTokens: 0,
        totalTokens: 0,
        estimatedCost: 0,
        timestamp: new Date(),
      });
    });

    this.emit('product:composed', { productId: product.id, capabilities });
  }

  /**
   * Inicia ciclo de vida do produto (P-063)
   */
  private startProductLifecycle(product: CognitiveProduct): void {
    const lifecycle = [
      { phase: 'necessidade', status: 'identified' },
      { phase: 'especialidade', status: 'mapped' },
      { phase: 'capacidade', status: 'composed' },
      { phase: 'produto', status: 'created' },
      { phase: 'operação', status: 'pending' },
      { phase: 'aprendizado', status: 'pending' },
      { phase: 'evolução', status: 'pending' },
    ];

    product.metadata.lifecycle = lifecycle;
    this.products.set(product.id, product);

    this.logger.info(`[ProductManager] Lifecycle started for product ${product.id}`);
    this.emit('product:lifecycle_started', { productId: product.id, lifecycle });
  }

  /**
   * Atualiza produto
   */
  updateProduct(id: string, updates: Partial<CognitiveProduct>): CognitiveProduct {
    const product = this.products.get(id);
    if (!product) {
      throw new Error(`Product ${id} not found`);
    }

    const updated = { ...product, ...updates, updatedAt: new Date() };
    this.products.set(id, updated);

    this.logger.info(`[ProductManager] Product updated: ${id}`);
    this.emit('product:updated', updated);

    return updated;
  }

  /**
   * Promove produto para produção
   */
  promoteToProduction(productId: string): CognitiveProduct {
    const product = this.products.get(productId);
    if (!product) {
      throw new Error(`Product ${productId} not found`);
    }

    product.status = 'production';
    product.version = this.incrementVersion(product.version);
    product.updatedAt = new Date();
    this.products.set(productId, product);

    this.logger.info(`[ProductManager] Product promoted to production: ${productId}`);
    this.emit('product:promoted', product);

    // P-063: Registra evolução
    this.cognitiveRepository.storeAsset({
      name: `Product: ${product.name} - Production`,
      type: 'capability',
      content: product,
      metadata: {
        author: 'ProductManager',
        tags: ['product', 'production', product.specialtyId],
        domain: product.specialtyId,
        confidence: 90,
        validationStatus: 'validated',
        source: 'ProductManager',
      },
    });

    return product;
  }

  /**
   * Incrementa versão
   */
  private incrementVersion(version: string): string {
    const parts = version.split('.');
    const patch = parseInt(parts[2] || '0') + 1;
    return `${parts[0]}.${parts[1]}.${patch}`;
  }

  /**
   * Obtém produto por ID
   */
  getProduct(id: string): CognitiveProduct | undefined {
    return this.products.get(id);
  }

  /**
   * Obtém produtos por especialidade
   */
  getProductsBySpecialty(specialtyId: string): CognitiveProduct[] {
    return Array.from(this.products.values())
      .filter((p) => p.specialtyId === specialtyId);
  }

  /**
   * Obtém produtos por status
   */
  getProductsByStatus(status: CognitiveProduct['status']): CognitiveProduct[] {
    return Array.from(this.products.values())
      .filter((p) => p.status === status);
  }

  /**
   * Obtém produtos em produção
   */
  getProductionProducts(): CognitiveProduct[] {
    return this.getProductsByStatus('production');
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    total: number;
    development: number;
    beta: number;
    production: number;
    deprecated: number;
    totalUsers: number;
    totalRevenue: number;
    avgSatisfaction: number;
    avgROI: number;
  } {
    const products = Array.from(this.products.values());
    const production = products.filter((p) => p.status === 'production');

    return {
      total: products.length,
      development: products.filter((p) => p.status === 'development').length,
      beta: products.filter((p) => p.status === 'beta').length,
      production: production.length,
      deprecated: products.filter((p) => p.status === 'deprecated').length,
      totalUsers: products.reduce((sum, p) => sum + p.metrics.users, 0),
      totalRevenue: products.reduce((sum, p) => sum + p.metrics.revenue, 0),
      avgSatisfaction: production.reduce((sum, p) => sum + p.metrics.satisfaction, 0) / (production.length || 1),
      avgROI: production.reduce((sum, p) => sum + p.metrics.roi, 0) / (production.length || 1),
    };
  }
}
