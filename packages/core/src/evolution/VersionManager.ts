import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-007: Sistema de versionamento genérico para qualquer "artefato" da
// plataforma (capacidade, decisão, ontologia, conhecimento, agente,
// workflow), com suporte a depreciação, arquivamento e comparação.

export type ArtifactType = 'capability' | 'decision' | 'ontology' | 'knowledge' | 'agent' | 'workflow';

export interface ArtifactVersion {
  id: string;
  artifactId: string;
  artifactType: ArtifactType;
  version: string; // ex.: 1.0.0
  content: any;
  changelog: string;
  status: 'active' | 'deprecated' | 'archived';
  createdAt: Date;
  createdBy?: string;
}

export class VersionManager extends EventEmitter {
  private versions: Map<string, ArtifactVersion[]> = new Map();
  private logger = getGlobalLogger();

  /**
   * Cria uma nova versão para um artefato, incrementando automaticamente
   * a versão semântica anterior caso nenhuma seja fornecida.
   */
  createVersion(params: {
    artifactId: string;
    artifactType: ArtifactType;
    content: any;
    changelog: string;
    version?: string;
    createdBy?: string;
  }): ArtifactVersion {
    const history = this.versions.get(params.artifactId) || [];
    const version = params.version || this.nextVersion(history);

    const artifactVersion: ArtifactVersion = {
      id: `ver_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      artifactId: params.artifactId,
      artifactType: params.artifactType,
      version,
      content: params.content,
      changelog: params.changelog,
      status: 'active',
      createdAt: new Date(),
      createdBy: params.createdBy,
    };

    // A versão anterior ativa passa a ser superada (mas não depreciada automaticamente)
    history.push(artifactVersion);
    this.versions.set(params.artifactId, history);

    this.logger.info(`[VersionManager] Nova versão criada: ${params.artifactId}@${version}`);
    this.emit('version:created', artifactVersion);
    return artifactVersion;
  }

  private nextVersion(history: ArtifactVersion[]): string {
    if (history.length === 0) return '1.0.0';
    const last = history[history.length - 1].version;
    const parts = last.split('.').map((n) => parseInt(n, 10) || 0);
    parts[2] = (parts[2] || 0) + 1;
    return parts.join('.');
  }

  deprecate(artifactId: string, version: string, reason: string): ArtifactVersion {
    const target = this.findVersion(artifactId, version);
    target.status = 'deprecated';
    this.logger.info(`[VersionManager] Versão depreciada: ${artifactId}@${version} — ${reason}`);
    this.emit('version:deprecated', { version: target, reason });
    return target;
  }

  archive(artifactId: string, version: string): ArtifactVersion {
    const target = this.findVersion(artifactId, version);
    target.status = 'archived';
    this.logger.info(`[VersionManager] Versão arquivada: ${artifactId}@${version}`);
    this.emit('version:archived', target);
    return target;
  }

  compareVersions(
    artifactId: string,
    versionA: string,
    versionB: string
  ): { changed: boolean; changelogA: string; changelogB: string } {
    const a = this.findVersion(artifactId, versionA);
    const b = this.findVersion(artifactId, versionB);
    return {
      changed: JSON.stringify(a.content) !== JSON.stringify(b.content),
      changelogA: a.changelog,
      changelogB: b.changelog,
    };
  }

  getVersionHistory(artifactId: string): ArtifactVersion[] {
    return this.versions.get(artifactId) || [];
  }

  getActiveVersion(artifactId: string): ArtifactVersion | undefined {
    const history = this.versions.get(artifactId) || [];
    return [...history].reverse().find((v) => v.status === 'active');
  }

  private findVersion(artifactId: string, version: string): ArtifactVersion {
    const history = this.versions.get(artifactId) || [];
    const found = history.find((v) => v.version === version);
    if (!found) {
      throw new Error(`Versão ${version} não encontrada para artefato ${artifactId}`);
    }
    return found;
  }
}
