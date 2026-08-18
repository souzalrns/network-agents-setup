import { Request, Response, NextFunction } from 'express';
import { getGlobalLogger } from '../Logger';
import { getGlobalMetrics } from '../Metrics';
export function loggingMiddleware(req: Request, res: Response, next: NextFunction): void {
  const start = Date.now();
  const logger = getGlobalLogger();
  const metrics = getGlobalMetrics();
  const requestId = (req.headers['x-request-id'] as string) || crypto.randomUUID();
  logger.info(`Request started: ${req.method} ${req.path}`, { requestId, method: req.method, path: req.path });
  const originalSend = res.send;
  res.send = function (body: any) {
    const duration = Date.now() - start;
    const level = res.statusCode >= 400 ? 'error' : 'info';
    logger.log(level, `Request completed: ${req.method} ${req.path}`, {
      requestId,
      method: req.method,
      path: req.path,
      status: res.statusCode,
      durationMs: duration,
    });
    metrics.counter('http_requests_total', { method: req.method, path: req.path, status: String(res.statusCode) });
    metrics.histogram('http_request_duration_ms', { method: req.method, path: req.path }, duration);
    return originalSend.call(this, body);
  };
  next();
}
