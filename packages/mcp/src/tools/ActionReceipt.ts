import { createHash } from 'crypto';
import { appendFileSync, existsSync, readFileSync } from 'fs';
import path from 'path';

/**
 * Recibo de acção com hash encadeado (C5, ADR-001 §4/§8, AUDIT-GOVERNANCE.md
 * §11 "Action Receipt: Construir no core").
 *
 * Escopo deliberadamente reduzido face ao contrato completo do ADR-001
 * (que inclui agent/principal como DID e uma AuthorizationDecision vinda
 * de Cedar/OPA) -- nada disso existe ainda neste repo (sem AgentMesh, sem
 * policy engine declarativo; `agentmesh-platform` nem é uma dependência
 * instalada, só foi revisto externamente durante a auditoria). Este módulo
 * regista o que o `ToolExecutor` já tem hoje (`caller` como string simples,
 * `hashParamsForAudit()` de `ToolPolicy.ts`), encadeado por hash -- não o
 * contrato completo de identidade/autorização, que depende da Fase 1 do
 * roadmap de `AUDIT-GOVERNANCE.md` §13 (ainda não feita).
 */
export interface ActionReceipt {
  actor: string;
  tool: string;
  params_hash: string;
  result_hash: string;
  prev_receipt_hash: string | null;
  at: string;
  receipt_hash: string;
}

type ReceiptFields = Omit<ActionReceipt, 'receipt_hash'>;

export function computeReceiptHash(receipt: ReceiptFields): string {
  return createHash('sha256')
    .update(
      JSON.stringify({
        actor: receipt.actor,
        tool: receipt.tool,
        params_hash: receipt.params_hash,
        result_hash: receipt.result_hash,
        prev_receipt_hash: receipt.prev_receipt_hash,
        at: receipt.at,
      })
    )
    .digest('hex');
}

export function hashResult(result: unknown): string {
  return createHash('sha256').update(JSON.stringify(result ?? null)).digest('hex');
}

export function receiptsLogPath(): string {
  const explicit = process.env.MCP_RECEIPTS_LOG_PATH;
  if (explicit) return explicit;
  const auditPath = process.env.MCP_AUDIT_LOG_PATH || path.resolve(process.cwd(), 'audit.jsonl');
  return `${auditPath}.chain`;
}

function readReceipts(logPath: string): ActionReceipt[] {
  if (!existsSync(logPath)) return [];
  return readFileSync(logPath, 'utf-8')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as ActionReceipt);
}

function latestReceiptHash(logPath: string): string | null {
  const receipts = readReceipts(logPath);
  return receipts.length ? receipts[receipts.length - 1].receipt_hash : null;
}

/**
 * Adiciona um recibo à cadeia (append-only, JSONL), calculando o hash a
 * partir do recibo anterior. Aditivo: nunca reescreve nem apaga linhas
 * existentes.
 */
export function appendReceipt(params: {
  actor: string;
  tool: string;
  params_hash: string;
  result_hash: string;
  logPath?: string;
}): ActionReceipt {
  const logPath = params.logPath ?? receiptsLogPath();
  const fields: ReceiptFields = {
    actor: params.actor,
    tool: params.tool,
    params_hash: params.params_hash,
    result_hash: params.result_hash,
    prev_receipt_hash: latestReceiptHash(logPath),
    at: new Date().toISOString(),
  };
  const receipt: ActionReceipt = { ...fields, receipt_hash: computeReceiptHash(fields) };
  appendFileSync(logPath, JSON.stringify(receipt) + '\n', { encoding: 'utf-8' });
  return receipt;
}

/**
 * Valida a cadeia inteira: cada recibo tem de apontar para o hash exacto
 * do anterior, e o próprio `receipt_hash` tem de bater com o recalculado
 * a partir dos campos. Cadeia vazia ou em falta é válida (nada para violar).
 */
export function verifyChain(logPath: string): { valid: boolean; broken_at?: number } {
  const receipts = readReceipts(logPath);
  let prevHash: string | null = null;
  for (let i = 0; i < receipts.length; i++) {
    const { receipt_hash, ...fields } = receipts[i];
    if (fields.prev_receipt_hash !== prevHash) {
      return { valid: false, broken_at: i };
    }
    if (computeReceiptHash(fields) !== receipt_hash) {
      return { valid: false, broken_at: i };
    }
    prevHash = receipt_hash;
  }
  return { valid: true };
}
