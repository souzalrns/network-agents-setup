import { EventEmitter } from 'events';
import {
  HitlRequest,
  HitlStatus,
  HitlPriority,
  HitlCategory,
} from '@network-agents/shared';
import { randomUUID } from 'crypto';
import { getGlobalLogger } from '@network-agents/observability';
export class HitlManager extends EventEmitter {
  private pendingRequests: Map<string, HitlRequest> = new Map();
  private approvedRequests: Map<string, HitlRequest> = new Map();
  private rejectedRequests: Map<string, HitlRequest> = new Map();
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
    const request = this.pendingRequests.get(requestId);
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
    const request = this.pendingRequests.get(requestId);
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
      this.rejectedRequests.get(requestId)
    );
  }
  isPending(requestId: string): boolean {
    return this.pendingRequests.has(requestId);
  }
  private scheduleExpiration(request: HitlRequest): void {
    if (!request.expiresAt) return;
    const timeout = request.expiresAt.getTime() - Date.now();
    if (timeout <= 0) {
      this.expireRequest(request.id);
      return;
    }
    setTimeout(() => {
      this.expireRequest(request.id);
    }, timeout);
  }
  private async expireRequest(requestId: string): Promise<void> {
    const request = this.pendingRequests.get(requestId);
    if (!request) return;
    request.status = HitlStatus.EXPIRED;
    this.pendingRequests.delete(requestId);
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
