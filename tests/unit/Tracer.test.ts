import { describe, it, expect } from 'vitest';
import { Tracer } from '../../packages/observability/src/Tracer';

describe('Tracer (D1 — memory leak fix)', () => {
  it('cria um span pai + span filho e exporta a trace correctamente', async () => {
    const tracer = new Tracer('test-service');
    const parentId = tracer.startSpan('parent-op');
    const childId = tracer.startSpan('child-op', parentId);

    tracer.setAttribute(childId, 'foo', 'bar');
    tracer.addEvent(childId, 'checkpoint');
    tracer.endSpan(childId, 'ok');
    tracer.endSpan(parentId, 'ok');

    const traceId = tracer.getTrace(parentId) ? parentId : undefined;
    // getTrace() e indexado por traceId, nao por spanId -- obter o traceId real.
    const allTraces = tracer.getAllTraces();
    expect(allTraces.size).toBe(1);
    const [realTraceId, spans] = [...allTraces.entries()][0];
    expect(spans).toHaveLength(2);
    expect(spans[0].name).toBe('parent-op');
    expect(spans[1].name).toBe('child-op');
    expect(spans[1].parentId).toBe(parentId);
    expect(spans[1].traceId).toBe(spans[0].traceId);
    expect(tracer.getTrace(realTraceId)).toHaveLength(2);

    // exportTrace nao deve lancar mesmo sem OTLP_ENDPOINT definida.
    await expect(tracer.exportTrace(realTraceId)).resolves.toBeUndefined();
  });

  it('endSpan liberta o span de currentSpans (nao acumula spans terminados)', () => {
    const tracer = new Tracer('test-service');
    const id = tracer.startSpan('op');
    tracer.endSpan(id);
    // addEvent/setAttribute apos endSpan sao no-op (span ja nao esta em currentSpans).
    tracer.setAttribute(id, 'k', 'v');
    const [, spans] = [...tracer.getAllTraces().entries()][0];
    expect(spans[0].attributes.k).toBeUndefined();
  });

  it('nao cresce sem limite: 1000+ traces em loop mantem o Map dentro de maxTraces', () => {
    const maxTraces = 200;
    const tracer = new Tracer('test-service', maxTraces);
    for (let i = 0; i < 1000; i++) {
      const id = tracer.startSpan(`op-${i}`);
      tracer.endSpan(id);
    }
    expect(tracer.getAllTraces().size).toBeLessThanOrEqual(maxTraces);
  });

  it('eviction e FIFO: as traces mais antigas desaparecem primeiro', () => {
    const tracer = new Tracer('test-service', 3);
    const ids = [0, 1, 2, 3, 4].map((i) => {
      const id = tracer.startSpan(`op-${i}`);
      tracer.endSpan(id);
      return id;
    });
    const remaining = new Set(
      [...tracer.getAllTraces().values()].map((spans) => spans[0].name)
    );
    expect(remaining.size).toBe(3);
    expect(remaining.has('op-0')).toBe(false);
    expect(remaining.has('op-1')).toBe(false);
    expect(remaining.has('op-4')).toBe(true);
    void ids;
  });

  it('mantem a API pública inalterada (não-regressão para Executor.ts)', () => {
    const tracer = new Tracer();
    expect(typeof tracer.startSpan).toBe('function');
    expect(typeof tracer.endSpan).toBe('function');
    expect(typeof tracer.setAttribute).toBe('function');
    expect(typeof tracer.addEvent).toBe('function');
    expect(typeof tracer.getTrace).toBe('function');
    expect(typeof tracer.exportTrace).toBe('function');
  });
});
