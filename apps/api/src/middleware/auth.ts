import { Request, Response, NextFunction } from 'express';
export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const apiKey = req.headers['x-api-key'];
  if (!process.env.API_KEY) {
    return next();
  }
  if (apiKey !== process.env.API_KEY) {
    res.status(401).json({ error: 'Invalid API key' });
    return;
  }
  next();
}
