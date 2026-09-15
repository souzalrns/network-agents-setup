import { describe, it, expect, vi, beforeEach } from 'vitest';
import { HitlManager } from '../../packages/core/src/hitl/HitlManager';
import { HitlStatus } from '@network-agents/shared';

describe('HitlManager', () => {
  let manager: HitlManager;

  beforeEach(() => {
    manager = new HitlManager({ autoExpireMinutes: 60 });
  });

  // -- requestApproval -------------------------------------------------------

  it('should create a pending request', async () => {
    const req = await manager.requestApproval({
      agentId: 'agent-1',
      domain: 'legal',
      category: 'legal' as any,
      priority: 'high' as any,
      title: 'Approve contract',
      description: 'Need approval',
      context: { foo: 'bar' },
      proposedAction: 'sign',
    });

    expect(req.id).toMatch(/^hitl_/);
    expect(req.status).toBe(HitlStatus.PENDING);
    expect(req.agentId).toBe('agent-1');
    expect(req.domain).toBe('legal');
    expect(req.title).toBe('Approve contract');
    expect(req.requestedAt).toBeInstanceOf(Date);
    expect(req.expiresAt).toBeInstanceOf(Date);
    expect(manager.isPending(req.id)).toBe(true);
  });

  it('should emit request-created event', async () => {
    const handler = vi.fn();
    manager.on('request-created', handler);

    await manager.requestApproval({
      agentId: 'agent-1',
      domain: 'legal',
      category: 'legal' as any,
      priority: 'high' as any,
      title: 'T',
      description: 'D',
      context: {},
      proposedAction: 'sign',
    });

    expect(handler).toHaveBeenCalledOnce();
    expect(handler.mock.calls[0][0].id).toMatch(/^hitl_/);
  });

  // -- approveRequest --------------------------------------------------------

  it('should approve a pending request', async () => {
    const req = await manager.requestApproval({
      agentId: 'a',
      domain: 'd',
      category: 'legal' as any,
      priority: 'low' as any,
      title: 'T',
      description: 'D',
      context: {},
      proposedAction: 'x',
    });

    const approved = await manager.approveRequest(req.id, 'user:luiz', 'ok');
    expect(approved.status).toBe(HitlStatus.APPROVED);
    expect(approved.responderId).toBe('user:luiz');
    expect(approved.responseComment).toBe('ok');
    expect(approved.respondedAt).toBeInstanceOf(Date);
    expect(manager.isPending(req.id)).toBe(false);
  });

  it('should throw when approving unknown request', async () => {
    await expect(manager.approveRequest('hitl_nope', 'u')).rejects.toThrow(
      /não encontrada|nao encontrada/i
    );
  });

  it('should throw when approving non-pending request', async () => {
    const req = await manager.requestApproval({
      agentId: 'a',
      domain: 'd',
      category: 'legal' as any,
      priority: 'low' as any,
      title: 'T',
      description: 'D',
      context: {},
      proposedAction: 'x',
    });
    await manager.approveRequest(req.id, 'u');
    await expect(manager.approveRequest(req.id, 'u2')).rejects.toThrow(
      /não está pendente|nao esta pendente/i
    );
  });

  // -- rejectRequest ---------------------------------------------------------

  it('should reject a pending request', async () => {
    const req = await manager.requestApproval({
      agentId: 'a',
      domain: 'd',
      category: 'legal' as any,
      priority: 'low' as any,
      title: 'T',
      description: 'D',
      context: {},
      proposedAction: 'x',
    });
    const rejected = await manager.rejectRequest(req.id, 'user:bob', 'no');
    expect(rejected.status).toBe(HitlStatus.REJECTED);
    expect(rejected.responseComment).toBe('no');
    expect(manager.isPending(req.id)).toBe(false);
  });

  // -- queries ---------------------------------------------------------------

  it('should list pending requests, optionally by domain', async () => {
    await manager.requestApproval({
      agentId: 'a', domain: 'legal', category: 'legal' as any,
      priority: 'low' as any, title: 'T1', description: 'D', context: {},
      proposedAction: 'x',
    });
    await manager.requestApproval({
      agentId: 'a', domain: 'marketing', category: 'strategic' as any,
      priority: 'low' as any, title: 'T2', description: 'D', context: {},
      proposedAction: 'x',
    });

    expect(manager.getPendingRequests()).toHaveLength(2);
    expect(manager.getPendingRequests('legal')).toHaveLength(1);
    expect(manager.getPendingRequests('nope')).toHaveLength(0);
  });

  it('should getRequest from pending, approved or rejected', async () => {
    const req = await manager.requestApproval({
      agentId: 'a', domain: 'd', category: 'legal' as any,
      priority: 'low' as any, title: 'T', description: 'D', context: {},
      proposedAction: 'x',
    });
    expect(manager.getRequest(req.id)?.id).toBe(req.id);

    await manager.approveRequest(req.id, 'u');
    expect(manager.getRequest(req.id)?.status).toBe(HitlStatus.APPROVED);

    expect(manager.getRequest('hitl_nope')).toBeUndefined();
  });

  // -- checkpoints -----------------------------------------------------------

  it('should save, get and clear checkpoints', async () => {
    const req = await manager.requestApproval({
      agentId: 'a', domain: 'd', category: 'legal' as any,
      priority: 'low' as any, title: 'T', description: 'D', context: {},
      proposedAction: 'x',
    });

    manager.saveCheckpoint({
      hitlRequestId: req.id,
      planId: 'plan-1',
      currentStepIndex: 2,
      executionState: { step: 'a' },
      memorySnapshot: { k: 'v' },
    });

    const cp = manager.getCheckpoint(req.id);
    expect(cp).toBeDefined();
    expect(cp.planId).toBe('plan-1');
    expect(cp.currentStepIndex).toBe(2);
    expect(cp.id).toMatch(/^cp_/);

    expect(manager.clearCheckpoint(req.id)).toBe(true);
    expect(manager.getCheckpoint(req.id)).toBeUndefined();
    expect(manager.clearCheckpoint(req.id)).toBe(false);
  });

  // -- expiration (BUG: expireRequest usa `request` nao definido) -------------

  it('should expire a request after its expiresAt', async () => {
    vi.useFakeTimers();
    try {
      const req = await manager.requestApproval({
        agentId: 'a', domain: 'd', category: 'legal' as any,
        priority: 'low' as any, title: 'T', description: 'D', context: {},
        proposedAction: 'x',
        expiresInMinutes: 1,
      });
      expect(manager.isPending(req.id)).toBe(true);

      // Avanca 61 segundos (1 minuto + margem).
      await vi.advanceTimersByTimeAsync(61 * 1000);

      expect(manager.isPending(req.id)).toBe(false);
      expect(manager.getRequest(req.id)?.status).toBe(HitlStatus.EXPIRED);
    } finally {
      vi.useRealTimers();
    }
  });
});