import { EventEmitter } from 'events';
import { readFileSync, writeFileSync } from 'fs';
import {
  HitlRequest,
  HitlStatus,
  HitlPriority,
  HitlCategory,
} from '@network-agents/shared';
import { randomUUID } from 'crypto';
import { getGlobalLogger } from '@network-agents/observability';

/** Traduz response interno (particípio) <-> contrato v1 (imperativo). 'edit' é igual dos dois lados. */
function responseToContract(response?: HitlRequest['response']): 'approve' | 'reject' | 'edit' | null {
  if (response === 'approved') return 'approve';
  if (response === 'rejected') return 'reject';
  if (response === 'edit') return 'edit';
  return null;
}
function responseFromContract(response: string | null | undefined): HitlRequest['response'] {
  if (response === 'approve') return 'approved';
  if (response === 'reject') return 'rejected';
  if (response === 'edit') return 'edit';
  return undefined;
}

/** Serializa um HitlRequest interno para o formato do contrato v1 (hitl-request-v1.json). */
function toContractRecord(request: HitlRequest): Record<string, any> {
  return {
    schema: 'hitl-request-v1',
    id: request.id,
    source: request.source ?? 'node_api',
    run_id: request.runId ?? null,
    plan_id: request.planId ?? null,
    step_id: request.stepId ?? null,
    agent_id: request.agentId ?? null,
    domain: request.domain ?? null,
    category: request.category ?? null,
    priority: request.priority,
    status: request.status,
    title: request.title,
    description: request.description ?? null,
    proposed_action: request.proposedAction ?? null,
    allow: request.allow ?? ['approve', 'reject'],
    context: request.context ?? {},
    alternatives: request.alternatives ?? [],
    risks: request.risks ?? [],
    impacts: request.impacts ?? [],
    requested_at: request.requestedAt.toISOString(),
    expires_at: request.expiresAt ? request.expiresAt.toISOString() : null,
    responded_at: request.respondedAt ? request.respondedAt.toISOString() : null,
    response: responseToContract(request.response),
    response_comment: request.responseComment ?? null,
    responder_id: request.responderId ?? null,
    metadata: request.metadata ?? {},
  };
}

/** Reconstrói um HitlRequest interno a partir de um registo no formato do contrato v1. */
function fromContractRecord(record: Record<string, any>): HitlRequest {
  return {
    id: record.id,
    agentId: record.agent_id ?? null,
    domain: record.domain ?? null,
    category: record.category ?? null,
    priority: record.priority ?? HitlPriority.MEDIUM,
    status: (record.status as HitlStatus) ?? HitlStatus.PENDING,
    title: record.title,
    description: record.description ?? null,
    context: record.context ?? {},
    proposedAction: record.proposed_action ?? null,
    alternatives: record.alternatives ?? [],
    risks: record.risks ?? [],
    impacts: record.impacts ?? [],
    requestedAt: new Date(record.requested_at),
    expiresAt: record.expires_at ? new Date(record.expires_at) : undefined,
    respondedAt: record.responded_at ? new Date(record.responded_at) : undefined,
    response: responseFromContract(record.response),
    responseComment: record.response_comment ?? undefined,
    responderId: record.responder_id ?? undefined,
    metadata: record.metadata ?? {},
    schema: 'hitl-request-v1',
    source: record.source,
    runId: record.run_id ?? null,
    planId: record.plan_id ?? null,
    stepId: record.step_id ?? null,
    allow: record.allow,
  };
}
export class HitlManager extends EventEmitter {
  private pendingRequests: Map<string, HitlRequest> = new Map();
  private approvedRequests: Map<string, HitlRequest> = new Map();
  private rejectedRequests: Map<string, HitlRequest> = new Map();
  private expiredRequests: Map<string, HitlRequest> = new Map();
  private checkpoints: Map<string, any> = new Map();
  private logger = getGlobalLogger();
  constructor(private options: { autoExpireMinutes?: number } = {}) {
    super();
    this.options.autoExpireMinutes = options.autoExpireMinutes || 60;
  }
  async requestApproval(params: {
    agentId: string;
    domain: string;
    category: HitlCategory;
    priority: HitlPriority;
    title: string;
    description: string;
    context: Record<string, any>;
    proposedAction: string;
    alternatives?: string[];
    risks?: string[];
    impacts?: string[];
    expiresInMinutes?: number;
    metadata?: Record<string, any>;
  }): Promise<HitlRequest> {
    const expiresIn = params.expiresInMinutes || this.options.autoExpireMinutes || 60;
    const request: HitlRequest = {
      id: `hitl_${randomUUID()}`,
      agentId: params.agentId,
      domain: params.domain,
      category: params.category,
      priority: params.priority,
      status: HitlStatus.PENDING,
      title: params.title,
      description: params.description,
      context: params.context,
      proposedAction: params.proposedAction,
      alternatives: params.alternatives,
      risks: params.risks,
      impacts: params.impacts,
      requestedAt: new Date(),
      expiresAt: new Date(Date.now() + expiresIn * 60 * 1000),
      metadata: params.metadata,
    };
    this.pendingRequests.set(request.id, request);
    this.emit('request-created', request);
    this.scheduleExpiration(request);
    this.logger.info('HITL request created', {
      id: request.id,
      domain: request.domain,
      category: request.category,
      priority: request.priority,
    });
    return request;
  }
  async approveRequest(
    requestId: string,
    responderId: string,
    comment?: string
  ): Promise<HitlRequest> {
    const request = this.getRequest(requestId);
    if (!request) {
      throw new Error(`Solicitação ${requestId} não encontrada`);
    }
    if (request.status !== HitlStatus.PENDING) {
      throw new Error(`Solicitação ${requestId} não está pendente`);
    }
    request.status = HitlStatus.APPROVED;
    request.respondedAt = new Date();
    request.response = 'approved';
    request.responseComment = comment;
    request.responderId = responderId;
    this.pendingRequests.delete(requestId);
    this.approvedRequests.set(requestId, request);
    this.emit('request-approved', request);
    this.logger.info('HITL request approved', { id: requestId, responderId });
    return request;
  }
  async rejectRequest(
    requestId: string,
    responderId: string,
    comment?: string
  ): Promise<HitlRequest> {
    const request = this.getRequest(requestId);
    if (!request) {
      throw new Error(`Solicitação ${requestId} não encontrada`);
    }
    if (request.status !== HitlStatus.PENDING) {
      throw new Error(`Solicitação ${requestId} não está pendente`);
    }
    request.status = HitlStatus.REJECTED;
    request.respondedAt = new Date();
    request.response = 'rejected';
    request.responseComment = comment;
    request.responderId = responderId;
    this.pendingRequests.delete(requestId);
    this.rejectedRequests.set(requestId, request);
    this.emit('request-rejected', request);
    this.logger.info('HITL request rejected', { id: requestId, responderId });
    return request;
  }
  getPendingRequests(domain?: string): HitlRequest[] {
    const requests = Array.from(this.pendingRequests.values());
    if (domain) {
      return requests.filter((r) => r.domain === domain);
    }
    return requests;
  }
  getRequest(requestId: string): HitlRequest | undefined {
    return (
      this.pendingRequests.get(requestId) ||
      this.approvedRequests.get(requestId) ||
      this.rejectedRequests.get(requestId) ||
      this.expiredRequests.get(requestId)
    );
  }
  isPending(requestId: string): boolean {
    return this.pendingRequests.has(requestId);
  }
  private mapForStatus(status: HitlStatus): Map<string, HitlRequest> {
    switch (status) {
      case HitlStatus.APPROVED:
        return this.approvedRequests;
      case HitlStatus.REJECTED:
        return this.rejectedRequests;
      case HitlStatus.EXPIRED:
      case HitlStatus.CANCELLED:
        return this.expiredRequests;
      default:
        return this.pendingRequests;
    }
  }
  /**
   * Lê um ficheiro JSONL no formato do contrato v1 (hitl-request-v1.json) —
   * tipicamente `hitl-requests.jsonl` escrito pelo `plan_runner` — e importa
   * cada pedido para o estado interno (mapa determinado pelo `status`).
   * Devolve os pedidos importados.
   */
  importFromFile(path: string): HitlRequest[] {
    const content = readFileSync(path, 'utf-8');
    const imported: HitlRequest[] = [];
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const record = JSON.parse(trimmed);
      const request = fromContractRecord(record);
      this.mapForStatus(request.status).set(request.id, request);
      imported.push(request);
    }
    return imported;
  }
  /**
   * Escreve todos os pedidos actualmente conhecidos (pendentes, aprovados,
   * rejeitados, expirados) para um ficheiro JSONL no formato do contrato v1,
   * um pedido por linha. Serve de contraparte a `importFromFile` e é o que o
   * `plan_runner` (lado Python) consegue reler como `hitl-requests.jsonl`.
   */
  exportToFile(path: string): void {
    const all = [
      ...this.pendingRequests.values(),
      ...this.approvedRequests.values(),
      ...this.rejectedRequests.values(),
      ...this.expiredRequests.values(),
    ];
    const lines = all.map((request) => JSON.stringify(toContractRecord(request)));
    writeFileSync(path, lines.length ? lines.join('\n') + '\n' : '', 'utf-8');
  }
  private scheduleExpiration(request: HitlRequest): void {
    if (!request.expiresAt) return;
    const timeout = request.expiresAt.getTime() - Date.now();
    if (timeout <= 0) {
      void this.expireRequest(request.id);
      return;
    }
    setTimeout(() => {
      void this.expireRequest(request.id);
    }, timeout);
  }
  private async expireRequest(requestId: string): Promise<void> {
    const request = this.pendingRequests.get(requestId);
    if (!request) return;
    request.status = HitlStatus.EXPIRED;
    this.pendingRequests.delete(requestId);
    this.expiredRequests.set(requestId, request);
    this.emit('request-expired', request);
    this.logger.info('HITL request expired', { id: requestId });
  }
  saveCheckpoint(params: {
    hitlRequestId: string;
    planId: string;
    currentStepIndex: number;
    executionState: Record<string, any>;
    memorySnapshot: Record<string, any>;
  }): void {
    const checkpoint = {
      id: `cp_${randomUUID()}`,
      hitlRequestId: params.hitlRequestId,
      planId: params.planId,
      currentStepIndex: params.currentStepIndex,
      executionState: params.executionState,
      memorySnapshot: params.memorySnapshot,
      createdAt: new Date(),
    };
    this.checkpoints.set(params.hitlRequestId, checkpoint);
    this.logger.info('HITL checkpoint saved', {
      hitlRequestId: params.hitlRequestId,
      planId: params.planId,
      currentStepIndex: params.currentStepIndex,
    });
  }
  getCheckpoint(hitlRequestId: string): any | undefined {
    return this.checkpoints.get(hitlRequestId);
  }
  clearCheckpoint(hitlRequestId: string): boolean {
    const existed = this.checkpoints.has(hitlRequestId);
    this.checkpoints.delete(hitlRequestId);
    if (existed) {
      this.logger.info('HITL checkpoint cleared', { hitlRequestId });
    }
    return existed;
  }
}