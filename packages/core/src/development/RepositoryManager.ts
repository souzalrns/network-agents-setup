import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SecurityManager } from '../security/SecurityManager';

export interface Repository {
  id: string;
  name: string;
  url: string;
  type: 'github' | 'gitlab' | 'bitbucket' | 'local';
  description: string;
  status: 'active' | 'archived' | 'deprecated' | 'quarantine';
  lastCommit?: string;
  lastCommitDate?: Date;
  stars?: number;
  forks?: number;
  license?: string;
  dependencies: string[];
  securityScore: number; // 0-100
  compatibilityScore: number; // 0-100
  costScore: number; // 0-100
  createdAt: Date;
  updatedAt: Date;
  metadata: Record<string, any>;
}

export interface RepositoryAnalysis {
  repositoryId: string;
  alignment: number; // 0-100
  dependencies: string[];
  vulnerabilities: string[];
  recommendations: string[];
  overallScore: number;
  approved: boolean;
}

export class RepositoryManager extends EventEmitter {
  private logger = getGlobalLogger();
  private repositories: Map<string, Repository> = new Map();
  private analyses: Map<string, RepositoryAnalysis> = new Map();

  constructor(_securityManager: SecurityManager) {
    super();
    this.logger.info('[RepositoryManager] Initialized');
    this.initializeDefaultRepositories();
  }

  /**
   * Inicializa repositórios padrão (P-052)
   */
  private initializeDefaultRepositories(): void {
    // P-052: Repositório para documentação da PCU
    // Nota de fidelidade: o material original passava também `id`, `createdAt`
    // e `updatedAt` aqui, mas registerRepository() já os gera automaticamente
    // e seu parâmetro é tipado como Omit<Repository, 'id'|'createdAt'|'updatedAt'>
    // — isso era um erro de compilação real (excesso de propriedades).
    this.registerRepository({
      name: 'PCU Documentação',
      url: 'https://github.com/network-agents/pcu-docs',
      type: 'github',
      description: 'Documentação da Plataforma Cognitiva Universal em Markdown',
      status: 'active',
      dependencies: [],
      securityScore: 90,
      compatibilityScore: 100,
      costScore: 100,
      metadata: {
        recommended: true,
        documentation: true,
      },
    });

    this.logger.info('[RepositoryManager] Default repositories initialized');
  }

  /**
   * Registra um repositório (P-052)
   */
  registerRepository(repo: Omit<Repository, 'id' | 'createdAt' | 'updatedAt'>): Repository {
    const id = `repo_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const fullRepo: Repository = {
      ...repo,
      id,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    this.repositories.set(id, fullRepo);
    this.logger.info(`[RepositoryManager] Repository registered: ${id}`);
    this.emit('repository:registered', fullRepo);

    return fullRepo;
  }

  /**
   * Verifica repositório automaticamente (P-053)
   */
  async verifyRepository(repositoryId: string): Promise<{
    exists: boolean;
    issues: string[];
    recommendations: string[];
  }> {
    this.logger.info(`[RepositoryManager] Verifying repository: ${repositoryId}`);

    const repo = this.repositories.get(repositoryId);
    if (!repo) {
      return {
        exists: false,
        issues: ['Repositório não encontrado'],
        recommendations: ['Registrar repositório antes de usar'],
      };
    }

    const issues: string[] = [];
    const recommendations: string[] = [];

    // Verifica se há dependências vulneráveis
    if (repo.dependencies.length > 0) {
      const vulnerabilities = await this.scanDependencies(repo.dependencies);
      if (vulnerabilities.length > 0) {
        issues.push(`Dependências vulneráveis: ${vulnerabilities.join(', ')}`);
        recommendations.push('Atualizar dependências para versões seguras');
      }
    }

    // Verifica segurança
    if (repo.securityScore < 70) {
      issues.push('Score de segurança baixo');
      recommendations.push('Revisar segurança do repositório');
    }

    // Verifica compatibilidade
    if (repo.compatibilityScore < 70) {
      issues.push('Baixa compatibilidade com a stack atual');
      recommendations.push('Avaliar compatibilidade técnica');
    }

    // Quarentena Tecnológica (P-054)
    if (repo.status === 'quarantine') {
      issues.push('Repositório em quarentena');
      recommendations.push('Avaliar antes de promover para produção');
    }

    return { exists: true, issues, recommendations };
  }

  /**
   * Analisa alinhamento do repositório (P-053)
   */
  analyzeRepositoryAlignment(repositoryId: string): RepositoryAnalysis {
    this.logger.info(`[RepositoryManager] Analyzing alignment: ${repositoryId}`);

    const repo = this.repositories.get(repositoryId);
    if (!repo) {
      throw new Error(`Repository ${repositoryId} not found`);
    }

    // Simula análise
    const alignment = 60 + Math.random() * 30;
    const dependencies = repo.dependencies || [];
    const vulnerabilities = this.scanDependencies(dependencies);

    const recommendations: string[] = [];
    if (alignment < 70) {
      recommendations.push('Melhorar alinhamento com a stack atual');
    }
    if (vulnerabilities.length > 0) {
      recommendations.push(`Corrigir vulnerabilidades: ${vulnerabilities.join(', ')}`);
    }
    if (repo.securityScore < 80) {
      recommendations.push('Revisar segurança do repositório');
    }

    const overallScore = (alignment + repo.securityScore + repo.compatibilityScore) / 3;
    const approved = overallScore >= 70 && vulnerabilities.length === 0;

    const analysis: RepositoryAnalysis = {
      repositoryId,
      alignment,
      dependencies,
      vulnerabilities,
      recommendations,
      overallScore,
      approved,
    };

    this.analyses.set(repositoryId, analysis);
    this.emit('repository:analyzed', analysis);

    return analysis;
  }

  /**
   * Aplica Quarentena Tecnológica (P-054)
   */
  applyQuarantine(repositoryId: string, reason: string): void {
    const repo = this.repositories.get(repositoryId);
    if (!repo) {
      throw new Error(`Repository ${repositoryId} not found`);
    }

    repo.status = 'quarantine';
    repo.metadata.quarantineReason = reason;
    repo.metadata.quarantineDate = new Date();
    this.repositories.set(repositoryId, repo);

    this.logger.info(`[RepositoryManager] Quarantine applied: ${repositoryId}`);
    this.emit('repository:quarantined', { repositoryId, reason });
  }

  /**
   * Autoingestão de conteúdo (P-055)
   */
  async autoIngestContent(repositoryId: string, content: any): Promise<{
    ingested: boolean;
    contentId: string;
    type: string;
  }> {
    this.logger.info(`[RepositoryManager] Auto-ingesting content: ${repositoryId}`);

    const repo = this.repositories.get(repositoryId);
    if (!repo) {
      throw new Error(`Repository ${repositoryId} not found`);
    }

    // Verifica conteúdo
    const contentType = this.detectContentType(content);
    const contentId = `content_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    // Autoingestão (P-055)
    this.emit('content:ingested', {
      repositoryId,
      contentId,
      contentType,
      timestamp: new Date(),
    });

    this.logger.info(`[RepositoryManager] Content auto-ingested: ${contentId}`);

    return {
      ingested: true,
      contentId,
      type: contentType,
    };
  }

  /**
   * Detecta tipo de conteúdo
   */
  private detectContentType(content: any): string {
    if (typeof content === 'string') {
      if (content.startsWith('{') || content.startsWith('[')) return 'json';
      if (content.startsWith('<')) return 'xml';
      if (content.startsWith('---')) return 'yaml';
      return 'text';
    }
    if (typeof content === 'object') {
      if (content instanceof Array) return 'array';
      return 'object';
    }
    return 'unknown';
  }

  /**
   * Escaneia dependências (P-053)
   */
  private scanDependencies(dependencies: string[]): string[] {
    // Simula escaneamento de vulnerabilidades
    const vulnerabilities: string[] = [];
    const vulnerable = ['lodash@1.0.0', 'express@3.0.0', 'axios@0.18.0'];
    for (const dep of dependencies) {
      if (vulnerable.some((v) => dep.includes(v))) {
        vulnerabilities.push(dep);
      }
    }
    return vulnerabilities;
  }

  /**
   * Obtém repositório por ID
   */
  getRepository(id: string): Repository | undefined {
    return this.repositories.get(id);
  }

  /**
   * Obtém todos os repositórios
   */
  getRepositories(): Repository[] {
    return Array.from(this.repositories.values());
  }

  /**
   * Obtém repositórios em quarentena
   */
  getQuarantinedRepositories(): Repository[] {
    return Array.from(this.repositories.values())
      .filter((r) => r.status === 'quarantine');
  }

  /**
   * Obtém análise por repositório
   */
  getAnalysis(repositoryId: string): RepositoryAnalysis | undefined {
    return this.analyses.get(repositoryId);
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalRepositories: number;
    activeRepositories: number;
    quarantinedRepositories: number;
    averageAlignment: number;
  } {
    const repos = Array.from(this.repositories.values());
    const active = repos.filter((r) => r.status === 'active');
    const quarantined = repos.filter((r) => r.status === 'quarantine');
    const analyses = Array.from(this.analyses.values());
    const avgAlignment = analyses.reduce((sum, a) => sum + a.alignment, 0) / (analyses.length || 1);

    return {
      totalRepositories: repos.length,
      activeRepositories: active.length,
      quarantinedRepositories: quarantined.length,
      averageAlignment: avgAlignment,
    };
  }
}
