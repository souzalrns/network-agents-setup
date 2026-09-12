import { Request, Response, NextFunction } from 'express';

/**
 * Autenticação fail-closed.
 *
 * Regra: sem API_KEY configurada, a API NÃO serve pedidos.
 *
 * A versão anterior fazia `if (!process.env.API_KEY) return next()` — ou seja,
 * um deploy sem a variável de ambiente deixava todos os endpoints abertos,
 * incluindo POST /hitl/:id/approve e /reject (qualquer pessoa poderia aprovar
 * um gate humano). Isso contradiz o princípio fail-closed que o resto do
 * projeto assume nos contratos de HITL.
 *
 * Para desenvolvimento local sem chave, é preciso optar explicitamente:
 *   ALLOW_UNAUTHENTICATED=true
 * Essa opção é ignorada quando NODE_ENV=production.
 */

function unauthenticatedAllowed(): boolean {
  return (
    process.env.ALLOW_UNAUTHENTICATED === 'true' &&
    process.env.NODE_ENV !== 'production'
  );
}

/**
 * Validação de arranque: chamar no bootstrap da API para falhar cedo,
 * em vez de só descobrir o problema no primeiro pedido.
 * Lança em produção; devolve aviso nos restantes ambientes.
 */
export function assertAuthConfig(): { ok: boolean; warning?: string } {
  if (process.env.API_KEY) return { ok: true };

  if (process.env.NODE_ENV === 'production') {
    throw new Error(
      'API_KEY em falta: a API recusa arrancar em produção sem autenticação configurada.'
    );
  }

  if (unauthenticatedAllowed()) {
    return {
      ok: true,
      warning:
        'A correr SEM autenticação (ALLOW_UNAUTHENTICATED=true). Nunca usar assim fora de desenvolvimento local.',
    };
  }

  return {
    ok: false,
    warning:
      'API_KEY em falta: todos os pedidos vão receber 503. Define API_KEY ou ALLOW_UNAUTHENTICATED=true para desenvolvimento local.',
  };
}

export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const configured = process.env.API_KEY;

  if (!configured) {
    if (unauthenticatedAllowed()) {
      next();
      return;
    }
    // Fail-closed: mal configurado = não serve.
    res.status(503).json({
      error: 'Service unavailable: authentication is not configured',
    });
    return;
  }

  const provided = req.headers['x-api-key'];

  if (typeof provided !== 'string' || !safeEqual(provided, configured)) {
    res.status(401).json({ error: 'Invalid API key' });
    return;
  }

  next();
}

/**
 * Comparação em tempo constante, para não vazar o tamanho/prefixo da chave
 * através da diferença de tempo de resposta.
 */
function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
