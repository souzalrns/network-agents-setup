export interface Span {
  id: string;
  traceId: string;
  parentId?: string;
  name: string;
  startTime: Date;
  endTime?: Date;
  durationMs?: number;
  status: 'ok' | 'error';
  attributes: Record<string, any>;
  events: Array<{ name: string; timestamp: Date; attributes: Record<string, any> }>;
}
export class Tracer {
  private traces: Map<string, Span[]> = new Map();
  private currentSpans: Map<string, Span> = new Map();
  private serviceName: string;
  constructor(serviceName: string = 'network-agents') {
    this.serviceName = serviceName;
  }
  startSpan(name: string, parentId?: string): string {
    const traceId = parentId ? this.getTraceId(parentId) || crypto.randomUUID() : crypto.randomUUID();
    const span: Span = {
      id: crypto.randomUUID(),
      traceId,
      parentId,
      name,
      startTime: new Date(),
      status: 'ok',
      attributes: { service: this.serviceName, name },
      events: [],
    };
    this.currentSpans.set(span.id, span);
    if (!this.traces.has(traceId)) this.traces.set(traceId, []);
    this.traces.get(traceId)!.push(span);
    return span.id;
  }
  endSpan(spanId: string, status: 'ok' | 'error' = 'ok', error?: Error): void {
    const span = this.currentSpans.get(spanId);
    if (!span) return;
    span.endTime = new Date();
    span.durationMs = span.endTime.getTime() - span.startTime.getTime();
    span.status = status;
    if (error) {
      span.attributes.error = error.message;
      span.attributes.stack = error.stack;
      span.events.push({ name: 'exception', timestamp: new Date(), attributes: { message: error.message } });
    }
    this.currentSpans.delete(spanId);
  }
  addEvent(spanId: string, name: string, attributes: Record<string, any> = {}): void {
    const span = this.currentSpans.get(spanId);
    if (!span) return;
    span.events.push({ name, timestamp: new Date(), attributes });
  }
  setAttribute(spanId: string, key: string, value: any): void {
    const span = this.currentSpans.get(spanId);
    if (!span) return;
    span.attributes[key] = value;
  }
  getTrace(traceId: string): Span[] | undefined {
    return this.traces.get(traceId);
  }
  getAllTraces(): Map<string, Span[]> {
    return this.traces;
  }
  private getTraceId(spanId: string): string | undefined {
    for (const [traceId, spans] of this.traces) {
      if (spans.some((s) => s.id === spanId)) return traceId;
    }
    return undefined;
  }
  async exportTrace(traceId: string): Promise<void> {
    const spans = this.traces.get(traceId);
    if (!spans) return;
    if (process.env.OTLP_ENDPOINT) {
      try {
        await fetch(process.env.OTLP_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resourceSpans: [{
              resource: { attributes: [{ key: 'service.name', value: { stringValue: this.serviceName } }] },
              scopeSpans: [{
                spans: spans.map((s) => ({
                  traceId: s.traceId,
                  spanId: s.id,
                  parentSpanId: s.parentId,
                  name: s.name,
                  startTimeUnixNano: s.startTime.getTime() * 1000000,
                  endTimeUnixNano: (s.endTime || new Date()).getTime() * 1000000,
                  status: { code: s.status === 'ok' ? 0 : 2 },
                })),
              }],
            }],
          }),
        });
      } catch (error) { console.error('Failed to export trace:', error); }
    }
  }
}
let globalTracer: Tracer | null = null;
export function getGlobalTracer(): Tracer {
  if (!globalTracer) globalTracer = new Tracer(process.env.SERVICE_NAME || 'network-agents');
  return globalTracer;
}
