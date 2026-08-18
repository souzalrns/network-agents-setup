import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { VersionManager } from '../evolution/VersionManager';
import { CognitiveRepository } from '../knowledge/CognitiveRepository';
import { SelfAwareness } from '../observability/SelfAwareness';

export interface DocumentVersion {
  id: string;
  title: string;
  version: string;
  content: string;
  status: 'draft' | 'review' | 'approved' | 'published' | 'archived';
  author: string;
  approver?: string;
  createdAt: Date;
  updatedAt: Date;
  publishedAt?: Date;
  changelog: string[];
  metadata: Record<string, any>;
}

export interface ConstitutionalAmendment {
  id: string;
  title: string;
  description: string;
  type: 'editorial' | 'update' | 'partial_reform' | 'structural_reform' | 'fundamental_reform';
  affectedArticles: string[];
  proposedBy: string;
  proposedAt: Date;
  status: 'proposed' | 'reviewing' | 'approved' | 'rejected' | 'implemented';
  reviewComments: string[];
  approvedBy?: string;
  approvedAt?: Date;
  implementedAt?: Date;
  metadata: Record<string, any>;
}

export class DocumentationGovernance extends EventEmitter {
  private logger = getGlobalLogger();
  private documentVersions: Map<string, DocumentVersion> = new Map();
  private amendments: Map<string, ConstitutionalAmendment> = new Map();

  constructor(
    private versionManager: VersionManager,
    private cognitiveRepository: CognitiveRepository,
    _selfAwareness: SelfAwareness
  ) {
    super();
    this.logger.info('[DocumentationGovernance] Initialized');
    this.initializeDocumentation();
  }

  /**
   * Inicializa documentação (P-064 a P-067)
   */
  private initializeDocumentation(): void {
    // P-064: Constituição como documento normativo permanente (Volume I)
    this.createDocumentVersion({
      title: 'Constituição da Plataforma Cognitiva Universal - Volume I',
      content: 'Este é o documento normativo permanente da PCU...',
      author: 'system',
      metadata: { volume: 'I', type: 'constitution' },
    });

    // P-065: Volume II - Teoria Geral
    this.createDocumentVersion({
      title: 'Teoria Geral das Organizações Cognitivas - Volume II',
      content: 'Fundamentos, conceitos e leis das Organizações Cognitivas...',
      author: 'system',
      metadata: { volume: 'II', type: 'theory' },
    });

    // P-066: Volume III - Engenharia
    this.createDocumentVersion({
      title: 'Engenharia da Plataforma - Volume III',
      content: 'Arquitetura, módulos, interfaces e implementação...',
      author: 'system',
      metadata: { volume: 'III', type: 'engineering' },
    });

    // P-067: Volume IV - Operação
    this.createDocumentVersion({
      title: 'Operação da Organização Cognitiva - Volume IV',
      content: 'Implantação, monitoramento e evolução em produção...',
      author: 'system',
      metadata: { volume: 'IV', type: 'operations' },
    });

    // P-069: Glossário Constitucional
    this.createDocumentVersion({
      title: 'Glossário Constitucional',
      content: 'Definições oficiais de todos os termos fundamentais...',
      author: 'system',
      metadata: { type: 'glossary' },
    });

    this.logger.info('[DocumentationGovernance] Documentation initialized');
  }

  /**
   * Cria uma versão de documento (P-064)
   */
  createDocumentVersion(data: {
    title: string;
    content: string;
    author: string;
    metadata?: Record<string, any>;
  }): DocumentVersion {
    const id = `doc_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const doc: DocumentVersion = {
      id,
      title: data.title,
      version: '1.0.0',
      content: data.content,
      status: 'draft',
      author: data.author,
      createdAt: new Date(),
      updatedAt: new Date(),
      changelog: ['Documento criado'],
      metadata: data.metadata || {},
    };

    this.documentVersions.set(id, doc);

    // Cria versão no version manager
    this.versionManager.createVersion(
      id,
      data.title,
      'knowledge',
      data.content,
      data.author,
      ['Documento criado'],
      { type: 'documentation' }
    );

    // Armazena no repositório cognitivo
    this.cognitiveRepository.storeAsset({
      name: `Documento: ${data.title}`,
      type: 'document',
      content: doc,
      metadata: {
        author: data.author,
        tags: ['documentation', data.metadata?.type || 'general'],
        domain: 'governance',
        confidence: 90,
        validationStatus: 'pending',
        source: 'DocumentationGovernance',
      },
    });

    this.logger.info(`[DocumentationGovernance] Document created: ${id}`);
    this.emit('document:created', doc);

    return doc;
  }

  /**
   * Atualiza documento (P-064)
   */
  updateDocument(docId: string, content: string, changelog: string): DocumentVersion {
    const doc = this.documentVersions.get(docId);
    if (!doc) {
      throw new Error(`Document ${docId} not found`);
    }

    doc.content = content;
    doc.version = this.incrementVersion(doc.version);
    doc.updatedAt = new Date();
    doc.changelog.push(changelog);

    this.documentVersions.set(docId, doc);

    // Atualiza versão
    this.versionManager.createVersion(
      docId,
      doc.title,
      'knowledge',
      content,
      'system',
      [changelog],
      { type: 'documentation' }
    );

    this.logger.info(`[DocumentationGovernance] Document updated: ${docId}`);
    this.emit('document:updated', doc);

    return doc;
  }

  /**
   * Aprova documento (publica)
   */
  approveDocument(docId: string, approver: string): DocumentVersion {
    const doc = this.documentVersions.get(docId);
    if (!doc) {
      throw new Error(`Document ${docId} not found`);
    }

    doc.status = 'approved';
    doc.approver = approver;
    doc.updatedAt = new Date();

    this.documentVersions.set(docId, doc);
    this.logger.info(`[DocumentationGovernance] Document approved: ${docId}`);
    this.emit('document:approved', doc);

    return doc;
  }

  /**
   * Publica documento
   */
  publishDocument(docId: string): DocumentVersion {
    const doc = this.documentVersions.get(docId);
    if (!doc) {
      throw new Error(`Document ${docId} not found`);
    }

    doc.status = 'published';
    doc.publishedAt = new Date();
    doc.updatedAt = new Date();

    this.documentVersions.set(docId, doc);
    this.logger.info(`[DocumentationGovernance] Document published: ${docId}`);
    this.emit('document:published', doc);

    return doc;
  }

  /**
   * Submete emenda constitucional (P-068)
   */
  submitAmendment(data: {
    title: string;
    description: string;
    type: ConstitutionalAmendment['type'];
    affectedArticles: string[];
    proposedBy: string;
    metadata?: Record<string, any>;
  }): ConstitutionalAmendment {
    const id = `amend_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const amendment: ConstitutionalAmendment = {
      id,
      title: data.title,
      description: data.description,
      type: data.type,
      affectedArticles: data.affectedArticles,
      proposedBy: data.proposedBy,
      proposedAt: new Date(),
      status: 'proposed',
      reviewComments: [],
      metadata: data.metadata || {},
    };

    this.amendments.set(id, amendment);
    this.logger.info(`[DocumentationGovernance] Amendment submitted: ${id}`);
    this.emit('amendment:submitted', amendment);

    return amendment;
  }

  /**
   * Revisa emenda (P-068)
   */
  reviewAmendment(amendmentId: string, comment: string): ConstitutionalAmendment {
    const amendment = this.amendments.get(amendmentId);
    if (!amendment) {
      throw new Error(`Amendment ${amendmentId} not found`);
    }

    amendment.status = 'reviewing';
    amendment.reviewComments.push(comment);
    this.amendments.set(amendmentId, amendment);

    this.logger.info(`[DocumentationGovernance] Amendment reviewed: ${amendmentId}`);
    this.emit('amendment:reviewed', amendment);

    return amendment;
  }

  /**
   * Aprova emenda (P-068)
   */
  approveAmendment(amendmentId: string, approver: string): ConstitutionalAmendment {
    const amendment = this.amendments.get(amendmentId);
    if (!amendment) {
      throw new Error(`Amendment ${amendmentId} not found`);
    }

    amendment.status = 'approved';
    amendment.approvedBy = approver;
    amendment.approvedAt = new Date();
    this.amendments.set(amendmentId, amendment);

    this.logger.info(`[DocumentationGovernance] Amendment approved: ${amendmentId}`);
    this.emit('amendment:approved', amendment);

    return amendment;
  }

  /**
   * Implementa emenda (P-068)
   */
  implementAmendment(amendmentId: string): ConstitutionalAmendment {
    const amendment = this.amendments.get(amendmentId);
    if (!amendment) {
      throw new Error(`Amendment ${amendmentId} not found`);
    }

    amendment.status = 'implemented';
    amendment.implementedAt = new Date();

    // Atualiza documentos afetados
    for (const article of amendment.affectedArticles) {
      const doc = Array.from(this.documentVersions.values()).find(
        (d) => d.title.includes(article) || d.metadata.article === article
      );
      if (doc) {
        this.updateDocument(
          doc.id,
          `${doc.content}\n\n[Atualizado pela Emenda ${amendmentId}]`,
          `Emenda ${amendmentId}: ${amendment.description}`
        );
      }
    }

    this.amendments.set(amendmentId, amendment);
    this.logger.info(`[DocumentationGovernance] Amendment implemented: ${amendmentId}`);
    this.emit('amendment:implemented', amendment);

    return amendment;
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
   * Obtém documento por ID
   */
  getDocument(id: string): DocumentVersion | undefined {
    return this.documentVersions.get(id);
  }

  /**
   * Obtém documentos publicados
   */
  getPublishedDocuments(): DocumentVersion[] {
    return Array.from(this.documentVersions.values())
      .filter((d) => d.status === 'published');
  }

  /**
   * Obtém emendas por status
   */
  getAmendmentsByStatus(status: ConstitutionalAmendment['status']): ConstitutionalAmendment[] {
    return Array.from(this.amendments.values())
      .filter((a) => a.status === status);
  }

  /**
   * Obtém emendas por tipo (P-068)
   */
  getAmendmentsByType(type: ConstitutionalAmendment['type']): ConstitutionalAmendment[] {
    return Array.from(this.amendments.values())
      .filter((a) => a.type === type);
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalDocuments: number;
    publishedDocuments: number;
    totalAmendments: number;
    approvedAmendments: number;
    implementedAmendments: number;
    byType: Record<ConstitutionalAmendment['type'], number>;
  } {
    const docs = Array.from(this.documentVersions.values());
    const amendments = Array.from(this.amendments.values());
    const byType: Record<ConstitutionalAmendment['type'], number> = {
      editorial: 0,
      update: 0,
      partial_reform: 0,
      structural_reform: 0,
      fundamental_reform: 0,
    };

    for (const a of amendments) {
      byType[a.type] = (byType[a.type] || 0) + 1;
    }

    return {
      totalDocuments: docs.length,
      publishedDocuments: docs.filter((d) => d.status === 'published').length,
      totalAmendments: amendments.length,
      approvedAmendments: amendments.filter((a) => a.status === 'approved').length,
      implementedAmendments: amendments.filter((a) => a.status === 'implemented').length,
      byType,
    };
  }
}
