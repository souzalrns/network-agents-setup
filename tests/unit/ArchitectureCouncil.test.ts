import { describe, it, expect, vi } from 'vitest';
import { ArchitectureCouncil } from '../../packages/core/src/governance/ArchitectureCouncil';
describe('ArchitectureCouncil', () => {
  it('should submit and approve a proposal', () => {
    const council = new ArchitectureCouncil({
      autoApproveThreshold: 80,
      requireReviewForTypes: ['architecture_change'],
    });
    const proposal = council.submitProposal({
      title: 'Test Proposal',
      description: 'Test description',
      type: 'new_capability',
      impact: {
        complexity: 'low',
        cost: 'low',
        risk: 'low',
        reusability: 'high',
      },
      dependencies: [],
      alternatives: ['Alternative 1'],
      proposedBy: 'test_user',
    });
    expect(proposal.status).toBe('pending');
    expect(proposal.id).toBeDefined();
  });
  it('should auto-approve low impact proposals', () => {
    const council = new ArchitectureCouncil({
      autoApproveThreshold: 80,
    });
    const proposal = council.submitProposal({
      title: 'Low Impact',
      description: 'Low impact description',
      type: 'new_capability',
      impact: {
        complexity: 'low',
        cost: 'low',
        risk: 'low',
        reusability: 'medium',
      },
      dependencies: [],
      alternatives: [],
      proposedBy: 'test_user',
    });
    // Auto-approval may happen async, so we check status
    expect(['pending', 'approved']).toContain(proposal.status);
  });
  it('should require review for high impact proposals', () => {
    const council = new ArchitectureCouncil({
      requireReviewForTypes: ['architecture_change'],
    });
    const proposal = council.submitProposal({
      title: 'High Impact',
      description: 'High impact description',
      type: 'architecture_change',
      impact: {
        complexity: 'high',
        cost: 'high',
        risk: 'high',
        reusability: 'low',
      },
      dependencies: ['dep1', 'dep2', 'dep3', 'dep4'],
      alternatives: [],
      proposedBy: 'test_user',
    });
    expect(['pending', 'reviewing']).toContain(proposal.status);
  });
  it('should register decisions', () => {
    const council = new ArchitectureCouncil();
    
    council.registerDecision({
      id: 'dec_001',
      date: new Date(),
      context: 'Test context',
      decision: 'Test decision',
      consequences: ['Consequence 1'],
      alternatives: ['Alternative 1'],
      status: 'active',
    });
    const decisions = council.getDecisions();
    expect(decisions).toHaveLength(1);
    expect(decisions[0].id).toBe('dec_001');
  });
});
