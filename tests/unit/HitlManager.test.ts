import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, writeFileSync, readFileSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
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

  // -- importFromFile / exportToFile (B4 / M2) -------------------------------

  describe('importFromFile / exportToFile (contrato v1)', () => {
    let dir: string;

    beforeEach(() => {
      dir = mkdtempSync(join(tmpdir(), 'hitl-b4-'));
    });

    afterEach(() => {
      rmSync(dir, { recursive: true, force: true });
    });

    it('round-trip: exporta um pedido pendente e reimporta-o num HitlManager limpo com os mesmos campos', async () => {
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

      const file = join(dir, 'hitl-requests.jsonl');
      manager.exportToFile(file);

      const fresh = new HitlManager();
      const imported = fresh.importFromFile(file);

      expect(imported).toHaveLength(1);
      const roundTripped = fresh.getRequest(req.id);
      expect(roundTripped).toBeDefined();
      expect(roundTripped?.id).toBe(req.id);
      expect(roundTripped?.agentId).toBe('agent-1');
      expect(roundTripped?.domain).toBe('legal');
      expect(roundTripped?.title).toBe('Approve contract');
      expect(roundTripped?.description).toBe('Need approval');
      expect(roundTripped?.proposedAction).toBe('sign');
      expect(roundTripped?.context).toEqual({ foo: 'bar' });
      expect(roundTripped?.status).toBe(HitlStatus.PENDING);
      expect(roundTripped?.requestedAt).toBeInstanceOf(Date);
      expect(fresh.isPending(req.id)).toBe(true);
    });

    it('round-trip: um pedido aprovado mantém o response e vai parar ao mapa correcto', async () => {
      const req = await manager.requestApproval({
        agentId: 'a', domain: 'd', category: 'legal' as any,
        priority: 'low' as any, title: 'T', description: 'D', context: {},
        proposedAction: 'x',
      });
      await manager.approveRequest(req.id, 'user:luiz', 'ok');

      const file = join(dir, 'hitl-requests.jsonl');
      manager.exportToFile(file);

      const fresh = new HitlManager();
      fresh.importFromFile(file);

      const roundTripped = fresh.getRequest(req.id);
      expect(roundTripped?.status).toBe(HitlStatus.APPROVED);
      expect(roundTripped?.response).toBe('approved');
      expect(roundTripped?.responderId).toBe('user:luiz');
      expect(roundTripped?.responseComment).toBe('ok');
      expect(fresh.isPending(req.id)).toBe(false);
    });

    it('importa um pedido real escrito pelo plan_runner (hitl.py), com agent_id/domain/category/description a null', () => {
      const record = {
        schema: 'hitl-request-v1',
        id: 'hitl_28c026ad-1f6e-4343-82b8-1ef4ec7e23c4',
        source: 'plan_runner',
        run_id: 'run_4f93ed84b6',
        plan_id: 'example-design-flow-demo',
        step_id: 'hitl',
        agent_id: null,
        domain: null,
        category: null,
        priority: 'medium',
        status: 'pending',
        title: "Approve step 'hitl' (plan_approve)",
        description: null,
        proposed_action: 'plan_approve',
        allow: ['approve', 'reject', 'edit'],
        context: { paused_at_step: 'hitl', completed: ['ux'], mode: 'stub' },
        alternatives: [],
        risks: [],
        impacts: [],
        requested_at: '2026-09-20T09:14:48.765344+00:00',
        expires_at: null,
        responded_at: null,
        response: null,
        response_comment: null,
        responder_id: null,
        metadata: {},
      };
      const file = join(dir, 'hitl-requests.jsonl');
      writeFileSync(file, JSON.stringify(record) + '\n', 'utf-8');

      const [imported] = manager.importFromFile(file);
      expect(imported.agentId).toBeNull();
      expect(imported.domain).toBeNull();
      expect(imported.category).toBeNull();
      expect(imported.description).toBeNull();
      expect(imported.runId).toBe('run_4f93ed84b6');
      expect(imported.planId).toBe('example-design-flow-demo');
      expect(imported.stepId).toBe('hitl');
      expect(imported.allow).toEqual(['approve', 'reject', 'edit']);
      expect(manager.isPending(imported.id)).toBe(true);
    });

    it('exportToFile traduz response interno (approved/rejected) para o vocabulário do contrato (approve/reject)', async () => {
      const req = await manager.requestApproval({
        agentId: 'a', domain: 'd', category: 'legal' as any,
        priority: 'low' as any, title: 'T', description: 'D', context: {},
        proposedAction: 'x',
      });
      await manager.rejectRequest(req.id, 'u');

      const file = join(dir, 'hitl-requests.jsonl');
      manager.exportToFile(file);

      const written = JSON.parse(readFileSync(file, 'utf-8').trim());
      expect(written.response).toBe('reject');
      expect(written.status).toBe('rejected');
    });
  });
});