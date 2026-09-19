import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

/**
 * Desenho novo inspirado no padrao de mcp/plan_runner/mcp_plan_runner/policy.py
 * (Python) -- nao e um porte 1:1: as tools sao diferentes (SCOPES abaixo cobre
 * read_file/write_file/list_directory/http_request/scrape_webpage/query_database,
 * nao list_templates/get_status/run_plan/resume_plan do lado Python) e alguns
 * campos (RateResult.remaining/reset_in, AuditEvent.params_hash, MCP_AUDIT_LOG_PATH
 * configuravel) sao melhorias conscientes sobre o original, nao equivalentes dele.
 *
 * Diferenca deliberada de perfil por omissao: o Python usa "moderate" por
 * omissao; aqui o omissao e "strict" -- fail-closed, consistente com
 * apps/api/src/middleware/auth.ts:assertAuthConfig().
 */

export type Profile = 'permissive' | 'moderate' | 'strict';

export interface AuthResult {
  allowed: boolean;
  reason: string;
  profile: Profile;
  caller: string;
}

export interface RateResult {
  allowed: boolean;
  remaining: number;
  reset_in: number;
}

export interface AuditEvent {
  caller: string;
  tool: string;
  params_hash: string;
  allowed: boolean;
  reason: string;
}

const SCOPES: Record<string, string> = {
  read_file: 'fs:file:read',
  write_file: 'fs:file:write',
  list_directory: 'fs:dir:list',
  http_request: 'net:http:request',
  scrape_webpage: 'net:http:scrape',
  query_database: 'db:query:execute',
};

// Mutating por razoes diferentes: write_file escreve em disco;
// query_database corre SQL arbitrario (pode escrever na base -- ver A4).
const MUTATING = new Set(['write_file', 'query_database']);

function profile(): Profile {
  const p = (process.env.MCP_POLICY_PROFILE || 'strict').trim().toLowerCase();
  return p === 'permissive' || p === 'moderate' ? p : 'strict';
}

function expectedKey(): string | undefined {
  const k = (process.env.MCP_POLICY_KEY || '').trim();
  return k || undefined;
}

function allowMutateEnv(): boolean {
  return ['1', 'true', 'yes'].includes(
    (process.env.MCP_POLICY_ALLOW_MUTATE || '').trim().toLowerCase()
  );
}

/**
 * Autoriza (ou nega) uma chamada a uma tool. `providedKey` e o 3o parametro
 * que o brief original nao previa em `authorize(caller, toolName)` -- foi
 * preciso acrescenta-lo para o caso "invalid_key" (chave fornecida errada)
 * ser sequer possivel, replicando o comportamento real do policy.py.
 */
export function authorize(caller: string, toolName: string, providedKey?: string): AuthResult {
  const prof = profile();
  const key = expectedKey();

  if (!(toolName in SCOPES)) {
    return { allowed: false, reason: 'unknown_tool', profile: prof, caller };
  }

  if (providedKey !== undefined && key && providedKey !== key) {
    return { allowed: false, reason: 'invalid_key', profile: prof, caller };
  }

  if (prof === 'permissive') {
    return { allowed: true, reason: 'permissive', profile: prof, caller };
  }

  if (!MUTATING.has(toolName)) {
    return { allowed: true, reason: 'read_ok', profile: prof, caller };
  }

  // A partir daqui, toolName e mutating.
  if (key) {
    return { allowed: true, reason: 'key_configured', profile: prof, caller };
  }

  if (allowMutateEnv()) {
    return { allowed: true, reason: 'allow_mutate_env', profile: prof, caller };
  }

  if (prof === 'moderate') {
    // eslint-disable-next-line no-console
    console.warn(
      `[SECURITY] moderate_lab_open: ${toolName} autorizado sem MCP_POLICY_KEY ` +
        `(caller=${caller}). So aceitavel em laboratorio local -- nunca expor ` +
        'este perfil fora disso.'
    );
    return { allowed: true, reason: 'moderate_lab_open', profile: prof, caller };
  }

  // strict (omissao)
  return { allowed: false, reason: 'strict_requires_key', profile: prof, caller };
}

const RATE_LIMIT = 60;
const RATE_WINDOW_MS = 60_000;
const rateBucket = new Map<string, number[]>();

export function rateLimit(
  caller: string,
  limit: number = RATE_LIMIT,
  windowMs: number = RATE_WINDOW_MS
): RateResult {
  const now = Date.now();
  const kept = (rateBucket.get(caller) ?? []).filter((t) => now - t < windowMs);

  if (kept.length >= limit) {
    rateBucket.set(caller, kept);
    const resetIn = Math.max(0, Math.ceil((windowMs - (now - kept[0])) / 1000));
    return { allowed: false, remaining: 0, reset_in: resetIn };
  }

  kept.push(now);
  rateBucket.set(caller, kept);
  return { allowed: true, remaining: limit - kept.length, reset_in: Math.ceil(windowMs / 1000) };
}

function paramsHash(params: Record<string, unknown>): string {
  return crypto
    .createHash('sha256')
    .update(JSON.stringify(params ?? {}))
    .digest('hex')
    .slice(0, 16);
}

function auditLogPath(): string {
  return process.env.MCP_AUDIT_LOG_PATH || path.resolve(process.cwd(), 'audit.jsonl');
}

export function audit(event: AuditEvent): void {
  const line = JSON.stringify({ at: new Date().toISOString(), ...event });
  fs.appendFileSync(auditLogPath(), line + '\n', { encoding: 'utf-8' });
}

export function hashParamsForAudit(params: Record<string, unknown>): string {
  return paramsHash(params);
}
