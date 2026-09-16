import { describe, it, expect } from 'vitest';
import { Router } from '../../packages/core/src/orchestrator/Router';

describe('Router', () => {
  const router = new Router();

  // -- route ----------------------------------------------------------------

  it('should route business keywords', () => {
    expect(router.route('preciso de uma proposta comercial')).toBe('business');
  });

  it('should route software keywords', () => {
    expect(router.route('quero um app frontend')).toBe('software');
  });

  it('should route medical keywords', () => {
    expect(router.route('paciente no hospital')).toBe('medical');
  });

  it('should route marketing keywords', () => {
    expect(router.route('campanha no instagram')).toBe('marketing');
  });

  it('should route construction keywords', () => {
    expect(router.route('reforma da obra')).toBe('construction');
  });

  it('should route legal keywords', () => {
    expect(router.route('contrato juridico')).toBe('legal');
  });

  it('should fallback to business when no keyword matches', () => {
    expect(router.route('xyz abc nada')).toBe('business');
  });

  it('should be case-insensitive', () => {
    expect(router.route('CAMPANHA')).toBe('marketing');
    expect(router.route('Contrato')).toBe('legal');
  });

  // -- routeWithConfidence --------------------------------------------------

  it('should return domain + confidence', () => {
    const result = router.routeWithConfidence('proposta comercial');
    expect(result.domain).toBe('business');
    expect(result.confidence).toBeGreaterThan(0);
    expect(result.confidence).toBeLessThanOrEqual(1);
  });

  it('should give higher confidence with more matches', () => {
    const one = router.routeWithConfidence('campanha');
    const two = router.routeWithConfidence('campanha conteudo instagram');
    expect(two.confidence).toBeGreaterThan(one.confidence);
  });

  it('should fallback to business with 0 confidence', () => {
    const result = router.routeWithConfidence('xyz abc nada');
    expect(result.domain).toBe('business');
    expect(result.confidence).toBe(0);
  });

  it('should be case-insensitive', () => {
    const upper = router.routeWithConfidence('CAMPANHA INSTAGRAM');
    const lower = router.routeWithConfidence('campanha instagram');
    expect(upper.domain).toBe(lower.domain);
    expect(upper.confidence).toBe(lower.confidence);
  });
});