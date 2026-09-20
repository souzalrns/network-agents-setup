import crypto from 'crypto';

/**
 * Autenticação HTTP fail-closed para MCPServer.createHttpHandler(), mesmo
 * padrão de apps/api/src/middleware/auth.ts:assertAuthConfig() (A18/A20),
 * adaptado para múltiplas chaves: cada chave configurada em MCP_SERVER_KEYS
 * é um caller distinto (Opção B do A8/S11 -- caller derivado da posse da
 * key, não de uma declaração não-autenticada tipo X-Caller-Id).
 *
 * Camada distinta de ToolPolicy.ts: aquele decide SE uma tool corre (scope +
 * MCP_POLICY_KEY, perfis permissive/moderate/strict); este decide SE o
 * pedido HTTP sequer chega lá, e QUEM é o chamador para o audit/rate-limit.
 */

export interface McpAuthResult {
  ok: boolean;
  caller?: string;
  reason?: string;
}

function configuredKeys(): string[] {
  return (process.env.MCP_SERVER_KEYS || '')
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean);
}

function unauthenticatedAllowed(): boolean {
  return (
    process.env.MCP_ALLOW_UNAUTHENTICATED === 'true' &&
    process.env.NODE_ENV !== 'production'
  );
}

/**
 * Validação de arranque -- mesmo propósito de assertAuthConfig(): falhar
 * cedo em produção sem chave configurada, em vez de só descobrir no
 * primeiro pedido.
 */
export function assertMcpAuthConfig(): { ok: boolean; warning?: string } {
  if (configuredKeys().length > 0) return { ok: true };

  if (process.env.NODE_ENV === 'production') {
    throw new Error(
      'MCP_SERVER_KEYS em falta: o MCPServer recusa arrancar em produção sem autenticação configurada.'
    );
  }

  if (unauthenticatedAllowed()) {
    return {
      ok: true,
      warning:
        'MCPServer a correr SEM autenticação (MCP_ALLOW_UNAUTHENTICATED=true). Nunca usar assim fora de desenvolvimento local.',
    };
  }

  return {
    ok: false,
    warning:
      'MCP_SERVER_KEYS em falta: todos os pedidos vão receber 503. Define MCP_SERVER_KEYS ou MCP_ALLOW_UNAUTHENTICATED=true para desenvolvimento local.',
  };
}

/** Comparação em tempo constante -- não vazar tamanho/prefixo por timing. */
function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

/** callerId estável e curto (8 chars) derivado da própria key -- duas keys
 * diferentes nunca colidem na prática (espaço de 32^8 hex a partir de sha256). */
export function callerIdFromKey(key: string): string {
  return crypto.createHash('sha256').update(key).digest('hex').slice(0, 8);
}

export function authenticateRequest(authorizationHeader: string | undefined): McpAuthResult {
  const keys = configuredKeys();

  if (keys.length === 0) {
    if (unauthenticatedAllowed()) {
      return { ok: true, caller: 'unauthenticated-dev' };
    }
    return { ok: false, reason: 'not_configured' };
  }

  if (!authorizationHeader || !authorizationHeader.startsWith('Bearer ')) {
    return { ok: false, reason: 'missing_bearer' };
  }

  const token = authorizationHeader.slice('Bearer '.length).trim();
  const matched = keys.find((k) => safeEqual(k, token));

  if (!matched) {
    return { ok: false, reason: 'invalid_key' };
  }

  return { ok: true, caller: callerIdFromKey(matched) };
}
