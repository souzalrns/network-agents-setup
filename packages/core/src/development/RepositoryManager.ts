import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { CompletenessValidator } from '../governance/CompletenessValidator';

// P-052 a P-055: Gestão de Repositórios Externos — registro, verificação
// (varredura simplificada de dependências vulneráveis), análise de
// alinhamento com a arquitetura da plataforma, status de "Quarentena
// Tecnológica" e ingestão automática de conteúdo do repositório.

export interface ExternalRepository {
  id: string;
  name: string;
  url: string;
  status: 'registered' | 'verifying' | 'quarantined' | 'approved' | 'rejected';
  alignmentScore: number; // 0-100
  vulnerabilities: string[];
  registeredAt: Date;
  verifiedAt?: Date;
}

export class RepositoryManager extends EventEmitter {
  private repositories: Map<string, ExternalRepository> = new Map();
  private logger = getGlobalLogger();

  constructor(private completenessValidator?: CompletenessValidator) {
    super();
  }

  registerRepository(name: string, url: string): ExternalRepository {
    const repo: ExternalRepository = {
      id: `repo_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name,
      url,
      status: 'registered',
      alignmentScore: 0,
      vulnerabilities: [],
      registeredAt: new Date(),
    };
    this.repositories.set(repo.id, repo);
    this.logger.info(`[RepositoryManager] Repositório registrado: ${name} (${url})`);
    this.emit('repository:registered', repo);
    return repo;
  }

  /**
   * Verifica um repositório: varre dependências em busca de
   * vulnerabilidades conhecidas e coloca em "Quarentena Tecnológica"
   * (P-054) caso alguma seja encontrada.
   */
  async verifyRepository(repoId: string, dependencies: string[]): Promise<ExternalRepository> {
    const repo = this.repositories.get(repoId);
    if (!repo) throw new Error(`Repositório ${repoId} não encontrado`);

    repo.status = 'verifying';
    this.repositories.set(repoId, repo);

    const vulnerabilities = this.scanDependencies(dependencies);
    repo.vulnerabilities = vulnerabilities;
    repo.verifiedAt = new Date();

    if (vulnerabilities.length > 0) {
      repo.status = 'quarantined';
      this.logger.warn(`[RepositoryManager] Repositório ${repo.name} colocado em quarentena tecnológica: ${vulnerabilities.join(', ')}`);
      this.emit('repository:quarantined', repo);
    } else {
      repo.status = 'approved';
      this.emit('repository:approved', repo);
    }

    this.repositories.set(repoId, repo);
    return repo;
  }

  private scanDependencies(dependencies: string[]): string[] {
    // Lista simplificada de padrões conhecidos como problemáticos.
    const knownVulnerable = ['event-stream', 'flatmap-stream', 'left-pad@0'];
    return dependencies.filter((dep) => knownVulnerable.some((v) => dep.includes(v)));
  }

  /**
   * Analisa o alinhamento de um repositório externo com os princípios
   * arquiteturais da plataforma (camadas, catálogo de capacidades,
   * pesquisa antes da construção).
   */
  analyzeAlignment(repoId: string, params: { hasLayeredArchitecture: boolean; hasDocumentation: boolean; testCoverage: number }): number {
    const repo = this.repositories.get(repoId);
    if (!repo) throw new Error(`Repositório ${repoId} não encontrado`);

    let score = 0;
    if (params.hasLayeredArchitecture) score += 40;
    if (params.hasDocumentation) score += 20;
    score += Math.min(params.testCoverage, 100) * 0.4;

    repo.alignmentScore = Math.round(score);
    this.repositories.set(repoId, repo);
    return repo.alignmentScore;
  }

  getQuarantinedRepositories(): ExternalRepository[] {
    return Array.from(this.repositories.values()).filter((r) => r.status === 'quarantined');
  }

  /**
   * Ingere o conteúdo (ex.: README, documentação) do repositório em uma
   * capacidade correspondente, quando um CompletenessValidator estiver
   * disponível.
   */
  async autoIngest(repoId: string, capabilityId: string, content: string): Promise<void> {
    const repo = this.repositories.get(repoId);
    if (!repo) throw new Error(`Repositório ${repoId} não encontrado`);
    if (repo.status !== 'approved') {
      throw new Error(`Repositório ${repo.name} não está aprovado para ingestão (status: ${repo.status})`);
    }
    if (!this.completenessValidator) {
      this.logger.warn('[RepositoryManager] Nenhum CompletenessValidator configurado, ingestão ignorada');
      return;
    }
    await this.completenessValidator.ingestContent(capabilityId, repo.url, 'documentation', content);
  }

  getRepository(id: string): ExternalRepository | undefined {
    return this.repositories.get(id);
  }

  getAllRepositories(): ExternalRepository[] {
    return Array.from(this.repositories.values());
  }
}
