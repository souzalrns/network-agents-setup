import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-064 a P-069: Governança Documental — volumes versionados do
// documento constitucional (I-IV) + glossário, e um fluxo completo de
// emenda constitucional (propor -> revisar -> aprovar -> implementar)
// com 5 tipos de emenda.

export interface DocumentVolume {
  id: 'I' | 'II' | 'III' | 'IV';
  title: string;
  version: string;
  content: string;
  updatedAt: Date;
}

export interface GlossaryEntry {
  term: string;
  definition: string;
}

export type AmendmentType = 'editorial' | 'update' | 'partial_reform' | 'structural_reform' | 'fundamental_reform';

export interface Amendment {
  id: string;
  volumeId: DocumentVolume['id'];
  type: AmendmentType;
  title: string;
  description: string;
  proposedText: string;
  status: 'proposed' | 'reviewing' | 'approved' | 'rejected' | 'implemented';
  proposedBy: string;
  createdAt: Date;
  reviewedAt?: Date;
  approvedAt?: Date;
  implementedAt?: Date;
}

const REQUIRED_APPROVAL_LEVEL: Record<AmendmentType, 'auto' | 'review' | 'council' | 'constitutional'> = {
  editorial: 'auto',
  update: 'review',
  partial_reform: 'council',
  structural_reform: 'council',
  fundamental_reform: 'constitutional',
};

export class DocumentationGovernance extends EventEmitter {
  private volumes: Map<string, DocumentVolume> = new Map();
  private glossary: Map<string, string> = new Map();
  private amendments: Map<string, Amendment> = new Map();
  private logger = getGlobalLogger();

  constructor() {
    super();
    this.initializeVolumes();
  }

  private initializeVolumes(): void {
    const defaults: Array<{ id: DocumentVolume['id']; title: string }> = [
      { id: 'I', title: 'Princípios Constitutivos' },
      { id: 'II', title: 'Arquitetura e Governança' },
      { id: 'III', title: 'Operação e Ciclo de Vida' },
      { id: 'IV', title: 'Ética, Segurança e Conformidade' },
    ];
    for (const v of defaults) {
      this.volumes.set(v.id, {
        id: v.id,
        title: v.title,
        version: '1.0.0',
        content: '',
        updatedAt: new Date(),
      });
    }
  }

  getVolume(id: DocumentVolume['id']): DocumentVolume | undefined {
    return this.volumes.get(id);
  }

  getAllVolumes(): DocumentVolume[] {
    return Array.from(this.volumes.values());
  }

  addGlossaryTerm(term: string, definition: string): void {
    this.glossary.set(term.toLowerCase(), definition);
  }

  getGlossaryTerm(term: string): string | undefined {
    return this.glossary.get(term.toLowerCase());
  }

  getGlossary(): GlossaryEntry[] {
    return Array.from(this.glossary.entries()).map(([term, definition]) => ({ term, definition }));
  }

  /**
   * Propõe uma emenda ao documento constitucional.
   */
  proposeAmendment(params: {
    volumeId: DocumentVolume['id'];
    type: AmendmentType;
    title: string;
    description: string;
    proposedText: string;
    proposedBy: string;
  }): Amendment {
    const amendment: Amendment = {
      id: `amend_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      ...params,
      status: 'proposed',
      createdAt: new Date(),
    };
    this.amendments.set(amendment.id, amendment);
    this.logger.info(`[DocumentationGovernance] Emenda proposta: ${amendment.title} (${amendment.type})`);
    this.emit('amendment:proposed', amendment);

    if (REQUIRED_APPROVAL_LEVEL[params.type] === 'auto') {
      return this.approveAmendment(amendment.id, 'system');
    }
    return amendment;
  }

  reviewAmendment(amendmentId: string, reviewer: string): Amendment {
    const amendment = this.requireAmendment(amendmentId);
    amendment.status = 'reviewing';
    amendment.reviewedAt = new Date();
    this.amendments.set(amendmentId, amendment);
    this.emit('amendment:reviewing', { amendment, reviewer });
    return amendment;
  }

  approveAmendment(amendmentId: string, approver: string): Amendment {
    const amendment = this.requireAmendment(amendmentId);
    amendment.status = 'approved';
    amendment.approvedAt = new Date();
    this.amendments.set(amendmentId, amendment);
    this.logger.info(`[DocumentationGovernance] Emenda aprovada: ${amendment.title} por ${approver}`);
    this.emit('amendment:approved', amendment);
    return amendment;
  }

  implementAmendment(amendmentId: string): Amendment {
    const amendment = this.requireAmendment(amendmentId);
    if (amendment.status !== 'approved') {
      throw new Error(`Emenda ${amendmentId} precisa estar aprovada antes de ser implementada (status atual: ${amendment.status})`);
    }
    const volume = this.volumes.get(amendment.volumeId);
    if (volume) {
      volume.content += `\n\n${amendment.proposedText}`;
      const parts = volume.version.split('.').map((n) => parseInt(n, 10) || 0);
      parts[1] = (parts[1] || 0) + 1;
      volume.version = parts.join('.');
      volume.updatedAt = new Date();
      this.volumes.set(amendment.volumeId, volume);
    }
    amendment.status = 'implemented';
    amendment.implementedAt = new Date();
    this.amendments.set(amendmentId, amendment);
    this.logger.info(`[DocumentationGovernance] Emenda implementada: ${amendment.title}`);
    this.emit('amendment:implemented', amendment);
    return amendment;
  }

  rejectAmendment(amendmentId: string, reason: string): Amendment {
    const amendment = this.requireAmendment(amendmentId);
    amendment.status = 'rejected';
    this.amendments.set(amendmentId, amendment);
    this.emit('amendment:rejected', { amendment, reason });
    return amendment;
  }

  private requireAmendment(id: string): Amendment {
    const amendment = this.amendments.get(id);
    if (!amendment) throw new Error(`Emenda ${id} não encontrada`);
    return amendment;
  }

  getAmendments(status?: Amendment['status']): Amendment[] {
    const all = Array.from(this.amendments.values());
    return status ? all.filter((a) => a.status === status) : all;
  }
}
