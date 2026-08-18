import { Request, Response, NextFunction } from 'express';
import { getGlobalTracer } from '../Tracer';
export function tracingMiddleware(req: Request, res: Response, next: NextFunction): void {
  const tracer = getGlobalTracer();
  const spanId = tracer.startSpan(`HTTP ${req.method} ${req.path}`);
  tracer.setAttribute(spanId, 'http.method', req.method);
  tracer.setAttribute(spanId, 'http.path', req.path);
  (req as any).traceSpanId = spanId;
  const originalSend = res.send;
  res.send = function (body: any) {
    const status = res.statusCode;
    tracer.setAttribute(spanId, 'http.status', status);
    tracer.endSpan(spanId, status >= 400 ? 'error' : 'ok');
    const trace = tracer.getTrace(spanId);
    if (trace) tracer.exportTrace(trace[0].traceId);
    return originalSend.call(this, body);
  };
  next();
}
