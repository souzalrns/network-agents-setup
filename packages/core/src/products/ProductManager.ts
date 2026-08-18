import { getGlobalLogger } from '@network-agents/observability';
import { SpecialtyManager } from '../domains/SpecialtyManager';

// P-061 a P-063: Gestão de Produtos Cognitivos — produtos compostos a
// partir das capacidades das especialidades, com ciclo de vida
// (necessidade -> especialidade -> capacidade -> produto -> operação ->
// aprendizado -> evolução) e promoção para produção.

export type ProductLifecycleStage =
  | 'necessidade'
  | 'especialidade'
  | 'capacidade'
  | 'produto'
  | 'operacao'
  | 'aprendizado'
  | 'evolucao';

export interface CognitiveProduct {
  id: string;
  name: string;
  domain: string;
  description: string;
  composedFrom: string[]; // ids de especialidades
  stage: ProductLifecycleStage;
  inProduction: boolean;
  createdAt: Date;
  updatedAt: Date;
}

const LIFECYCLE_ORDER: ProductLifecycleStage[] = [
  'necessidade',
  'especialidade',
  'capacidade',
  'produto',
  'operacao',
  'aprendizado',
  'evolucao',
];

const DEFAULT_PRODUCTS: Array<{ name: string; domain: string; description: string }> = [
  { name: 'Assistente de Revisão Contratual', domain: 'legal', description: 'Revisa contratos e sinaliza cláusulas de risco.' },
  { name: 'Diagnóstico HVAC Inteligente', domain: 'hvac', description: 'Diagnostica falhas em sistemas de climatização.' },
  { name: 'Orçamentista de Obras', domain: 'construction', description: 'Gera orçamentos preliminares de obras.' },
  { name: 'Gerador de Campanhas', domain: 'marketing', description: 'Cria campanhas de marketing personalizadas.' },
  { name: 'Triagem Clínica Assistida', domain: 'medicine', description: 'Auxilia triagem inicial de sintomas.' },
  { name: 'Monitor de Compliance', domain: 'legal', description: 'Monitora conformidade regulatória contínua.' },
  { name: 'Otimizador de Conteúdo SEO', domain: 'marketing', description: 'Otimiza conteúdo para mecanismos de busca.' },
];

export class ProductManager {
  private products: Map<string, CognitiveProduct> = new Map();
  private logger = getGlobalLogger();

  constructor(private specialtyManager: SpecialtyManager) {
    this.registerDefaultProducts();
  }

  private registerDefaultProducts(): void {
    for (const p of DEFAULT_PRODUCTS) {
      const specialty = this.specialtyManager.getSpecialty(p.domain);
      this.createProduct({
        name: p.name,
        domain: p.domain,
        description: p.description,
        composedFrom: specialty ? [specialty.id] : [],
      });
    }
  }

  createProduct(params: { name: string; domain: string; description: string; composedFrom: string[] }): CognitiveProduct {
    const product: CognitiveProduct = {
      id: `prod_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: params.name,
      domain: params.domain,
      description: params.description,
      composedFrom: params.composedFrom,
      stage: 'necessidade',
      inProduction: false,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.products.set(product.id, product);
    this.logger.info(`[ProductManager] Produto cognitivo criado: ${product.name}`);
    return product;
  }

  advanceStage(productId: string): CognitiveProduct {
    const product = this.products.get(productId);
    if (!product) throw new Error(`Produto ${productId} não encontrado`);
    const idx = LIFECYCLE_ORDER.indexOf(product.stage);
    if (idx < LIFECYCLE_ORDER.length - 1) {
      product.stage = LIFECYCLE_ORDER[idx + 1];
      product.updatedAt = new Date();
      this.products.set(productId, product);
      this.logger.info(`[ProductManager] Produto ${product.name} avançou para "${product.stage}"`);
    }
    return product;
  }

  /**
   * Promove um produto para produção quando ele atinge o estágio "operacao".
   */
  promoteToProduction(productId: string): CognitiveProduct {
    const product = this.products.get(productId);
    if (!product) throw new Error(`Produto ${productId} não encontrado`);
    const idx = LIFECYCLE_ORDER.indexOf(product.stage);
    const operacaoIdx = LIFECYCLE_ORDER.indexOf('operacao');
    if (idx < operacaoIdx) {
      throw new Error(`Produto ${product.name} ainda não atingiu o estágio "operacao" (atual: ${product.stage})`);
    }
    product.inProduction = true;
    product.updatedAt = new Date();
    this.products.set(productId, product);
    this.logger.info(`[ProductManager] Produto ${product.name} promovido para produção`);
    return product;
  }

  getProduct(id: string): CognitiveProduct | undefined {
    return this.products.get(id);
  }

  getAllProducts(): CognitiveProduct[] {
    return Array.from(this.products.values());
  }

  getProductsInProduction(): CognitiveProduct[] {
    return this.getAllProducts().filter((p) => p.inProduction);
  }
}
