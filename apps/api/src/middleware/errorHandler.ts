import { Request, Response, NextFunction } from 'express';
import { toClientError } from '../utils/sanitizeError';

export function errorHandler(
  err: any,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  const status = err.status || 500;
  const message = toClientError(err, 'ao processar pedido');
  res.status(status).json({
    error: message,
    timestamp: new Date().toISOString(),
    path: req.path,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
}
