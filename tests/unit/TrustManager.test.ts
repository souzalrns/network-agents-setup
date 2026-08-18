import { describe, it, expect } from 'vitest';
import { TrustManager } from '../../packages/core/src/governance/TrustManager';
describe('TrustManager', () => {
  it('should propose a competence', () => {
    const manager = new TrustManager();
    const competence = manager.proposeCompetence({
      name: 'Test Competence',
      description: 'Test description',
      domain: 'test',
      initialTrustLevel: 'level_0',
      evidence: ['Evidence 1'],
    });
    expect(competence.id).toBeDefined();
    expect(competence.status).toBe('proposed');
  });
  it('should evaluate a competence', () => {
    const manager = new TrustManager();
    const competence = manager.proposeCompetence({
      name: 'Test Competence',
      description: 'Test description',
      domain: 'test',
      initialTrustLevel: 'level_0',
      evidence: ['Evidence 1', 'Evidence 2', 'Evidence 3'],
    });
    const result = manager.evaluateCompetence(competence.id);
    
    expect(result).toHaveProperty('passed');
    expect(result).toHaveProperty('trustLevel');
    expect(result).toHaveProperty('metrics');
  });
  it('should set autonomy boundary', () => {
    const manager = new TrustManager();
    const competence = manager.proposeCompetence({
      name: 'Test Competence',
      description: 'Test description',
      domain: 'test',
    });
    manager.setAutonomyBoundary(competence.id, {
      financialLimit: 1000,
      operationalScope: ['scope1', 'scope2'],
      legalRestrictions: [],
      ethicalConstraints: [],
      riskTolerance: 'medium',
      escalationThreshold: 50,
    });
    const check = manager.checkAutonomy(competence.id, {
      type: 'test_action',
      financialImpact: 500,
      scope: 'scope1',
    });
    expect(check.allowed).toBe(true);
  });
  it('should check autonomy limits', () => {
    const manager = new TrustManager();
    const competence = manager.proposeCompetence({
      name: 'Test Competence',
      description: 'Test description',
      domain: 'test',
    });
    manager.setAutonomyBoundary(competence.id, {
      financialLimit: 1000,
      operationalScope: ['scope1'],
      legalRestrictions: [],
      ethicalConstraints: [],
      riskTolerance: 'low',
      escalationThreshold: 50,
    });
    const check = manager.checkAutonomy(competence.id, {
      type: 'test_action',
      financialImpact: 2000,
      scope: 'scope1',
    });
    expect(check.allowed).toBe(false);
    expect(check.requiresEscalation).toBe(true);
  });
});
