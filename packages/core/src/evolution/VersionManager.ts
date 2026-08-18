import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

export interface VersionedArtifact {
  id: string;
  name: string;
  type: 'capability' | 'decision' | 'ontology' | 'knowledge' | 'agent' | 'workflow';
  version: string;
  previousVersion?: string;
  content: any;
  changes: string[];
  author: string;
  timestamp: Date;
  status: 'draft' | 'active' | 'deprecated' | 'archived';
  metadata: Record<string, any>;
}

export interface VersionHistory {
  artifactId: string;
  versions: VersionedArtifact[];
  currentVersion: string;
  createdAt: Date;
  updatedAt: Date;
}

export class VersionManager extends EventEmitter {
  private logger = getGlobalLogger();
  private artifacts: Map<string, VersionHistory> = new Map();
  private versionCounter: Map<string, number> = new Map();

  constructor() {
    super();
    this.logger.info('[VersionManager] Initialized');
  }

  /**
   * Cria uma nova versão de um artefato
   */
  createVersion(
    artifactId: string,
    name: string,
    type: VersionedArtifact['type'],
    content: any,
    author: string,
    changes: string[],
    metadata: Record<string, any> = {}
  ): VersionedArtifact {
    // Obtém ou inicializa histórico
    let history = this.artifacts.get(artifactId);
    if (!history) {
      history = {
        artifactId,
        versions: [],
        currentVersion: '0.0.0',
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      this.artifacts.set(artifactId, history);
      this.versionCounter.set(artifactId, 0);
    }

    // Incrementa versão
    const counter = (this.versionCounter.get(artifactId) || 0) + 1;
    this.versionCounter.set(artifactId, counter);
    const version = `1.${counter}.0`;

    // Cria artefato versionado
    const artifact: VersionedArtifact = {
      id: `${artifactId}@${version}`,
      name,
      type,
      version,
      previousVersion: history.currentVersion !== '0.0.0' ? history.currentVersion : undefined,
      content,
      changes,
      author,
      timestamp: new Date(),
      status: 'active',
      metadata,
    };

    // Adiciona ao histórico
    history.versions.push(artifact);
    history.currentVersion = version;
    history.updatedAt = new Date();
    this.artifacts.set(artifactId, history);

    this.logger.info(`[VersionManager] New version created: ${artifactId}@${version}`);
    this.emit('version:created', artifact);

    return artifact;
  }

  /**
   * Obtém versão atual de um artefato
   */
  getCurrentVersion(artifactId: string): VersionedArtifact | undefined {
    const history = this.artifacts.get(artifactId);
    if (!history) return undefined;

    return history.versions.find((v) => v.version === history.currentVersion);
  }

  /**
   * Obtém versão específica de um artefato
   */
  getVersion(artifactId: string, version: string): VersionedArtifact | undefined {
    const history = this.artifacts.get(artifactId);
    if (!history) return undefined;

    return history.versions.find((v) => v.version === version);
  }

  /**
   * Obtém todas as versões de um artefato
   */
  getVersionHistory(artifactId: string): VersionHistory | undefined {
    return this.artifacts.get(artifactId);
  }

  /**
   * Lista todos os artefatos versionados
   */
  listArtifacts(type?: VersionedArtifact['type']): VersionedArtifact[] {
    const all: VersionedArtifact[] = [];
    for (const history of this.artifacts.values()) {
      const current = history.versions.find((v) => v.version === history.currentVersion);
      if (current && (!type || current.type === type)) {
        all.push(current);
      }
    }
    return all;
  }

  /**
   * Deprecia uma versão
   */
  deprecateVersion(artifactId: string, version: string, reason: string): void {
    const history = this.artifacts.get(artifactId);
    if (!history) {
      throw new Error(`Artifact ${artifactId} not found`);
    }

    const artifact = history.versions.find((v) => v.version === version);
    if (!artifact) {
      throw new Error(`Version ${version} not found for ${artifactId}`);
    }

    artifact.status = 'deprecated';
    artifact.metadata.deprecationReason = reason;
    artifact.metadata.deprecatedAt = new Date();

    this.artifacts.set(artifactId, history);
    this.logger.info(`[VersionManager] Version deprecated: ${artifactId}@${version}`);
    this.emit('version:deprecated', artifact);
  }

  /**
   * Arquiva uma versão
   */
  archiveVersion(artifactId: string, version: string): void {
    const history = this.artifacts.get(artifactId);
    if (!history) {
      throw new Error(`Artifact ${artifactId} not found`);
    }

    const artifact = history.versions.find((v) => v.version === version);
    if (!artifact) {
      throw new Error(`Version ${version} not found for ${artifactId}`);
    }

    artifact.status = 'archived';
    this.artifacts.set(artifactId, history);
    this.logger.info(`[VersionManager] Version archived: ${artifactId}@${version}`);
    this.emit('version:archived', artifact);
  }

  /**
   * Compara duas versões
   */
  compareVersions(artifactId: string, version1: string, version2: string): {
    differences: string[];
    similarity: number;
  } {
    const v1 = this.getVersion(artifactId, version1);
    const v2 = this.getVersion(artifactId, version2);

    if (!v1 || !v2) {
      throw new Error('Version not found');
    }

    // Calcula similaridade simplificada
    const content1 = JSON.stringify(v1.content);
    const content2 = JSON.stringify(v2.content);

    const differences: string[] = [];
    if (content1 !== content2) {
      differences.push('Conteúdo alterado');
    }

    if (v1.name !== v2.name) {
      differences.push(`Nome alterado: ${v1.name} -> ${v2.name}`);
    }

    if (v1.type !== v2.type) {
      differences.push(`Tipo alterado: ${v1.type} -> ${v2.type}`);
    }

    // Similaridade simples
    const similarity = content1 === content2 ? 100 : 50;

    return { differences, similarity };
  }

  /**
   * Obtém estatísticas de versionamento
   */
  getStats(): {
    totalArtifacts: number;
    totalVersions: number;
    activeVersions: number;
    deprecatedVersions: number;
    archivedVersions: number;
    byType: Record<VersionedArtifact['type'], number>;
  } {
    const stats = {
      totalArtifacts: this.artifacts.size,
      totalVersions: 0,
      activeVersions: 0,
      deprecatedVersions: 0,
      archivedVersions: 0,
      byType: {} as Record<VersionedArtifact['type'], number>,
    };

    // Inicializa contadores por tipo
    const types: VersionedArtifact['type'][] = ['capability', 'decision', 'ontology', 'knowledge', 'agent', 'workflow'];
    for (const type of types) {
      stats.byType[type] = 0;
    }

    for (const history of this.artifacts.values()) {
      for (const version of history.versions) {
        stats.totalVersions++;
        if (version.status === 'active') stats.activeVersions++;
        if (version.status === 'deprecated') stats.deprecatedVersions++;
        if (version.status === 'archived') stats.archivedVersions++;
        stats.byType[version.type] = (stats.byType[version.type] || 0) + 1;
      }
    }

    return stats;
  }
}
