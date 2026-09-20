import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, readFileSync, writeFileSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import { appendReceipt, computeReceiptHash, hashResult, verifyChain } from '../../packages/mcp/src/tools/ActionReceipt';

describe('ActionReceipt (C5 — hash encadeado)', () => {
  let dir: string;
  let logPath: string;

  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), 'action-receipt-'));
    logPath = join(dir, 'receipts.jsonl');
  });

  afterEach(() => {
    rmSync(dir, { recursive: true, force: true });
  });

  it('a 3ª acção depende do conteúdo das 2 anteriores (cadeia real)', () => {
    const r1 = appendReceipt({ actor: 'a', tool: 'read_file', params_hash: 'p1', result_hash: hashResult('ok1'), logPath });
    const r2 = appendReceipt({ actor: 'a', tool: 'write_file', params_hash: 'p2', result_hash: hashResult('ok2'), logPath });
    const r3 = appendReceipt({ actor: 'a', tool: 'query_database', params_hash: 'p3', result_hash: hashResult('ok3'), logPath });

    expect(r1.prev_receipt_hash).toBeNull();
    expect(r2.prev_receipt_hash).toBe(r1.receipt_hash);
    expect(r3.prev_receipt_hash).toBe(r2.receipt_hash);

    // r3 depende de r2 que depende de r1 -- mudar qualquer campo de r1 muda
    // o hash esperado de r2 (mesmo sem re-escrever r2), o que verifyChain
    // apanha (ver teste seguinte). Aqui confirmamos a dependência directa:
    // recalcular o hash de r3 com um prev_receipt_hash diferente dá outro valor.
    const tamperedR3Hash = computeReceiptHash({ ...r3, prev_receipt_hash: 'outro-hash-qualquer' });
    expect(tamperedR3Hash).not.toBe(r3.receipt_hash);

    const chain = readFileSync(logPath, 'utf-8').trim().split('\n');
    expect(chain).toHaveLength(3);
    expect(verifyChain(logPath)).toEqual({ valid: true });
  });

  it('adulterar um recibo do meio é detectado por verifyChain()', () => {
    appendReceipt({ actor: 'a', tool: 'read_file', params_hash: 'p1', result_hash: 'r1', logPath });
    appendReceipt({ actor: 'a', tool: 'write_file', params_hash: 'p2', result_hash: 'r2', logPath });
    appendReceipt({ actor: 'a', tool: 'query_database', params_hash: 'p3', result_hash: 'r3', logPath });

    const lines = readFileSync(logPath, 'utf-8').trim().split('\n');
    const middle = JSON.parse(lines[1]);
    middle.result_hash = 'adulterado';
    lines[1] = JSON.stringify(middle);
    writeFileSync(logPath, lines.join('\n') + '\n', 'utf-8');

    const result = verifyChain(logPath);
    expect(result.valid).toBe(false);
    expect(result.broken_at).toBe(1);
  });

  it('cadeia vazia ou inexistente devolve valid:true', () => {
    expect(verifyChain(logPath)).toEqual({ valid: true });
    expect(verifyChain(join(dir, 'nao-existe.jsonl'))).toEqual({ valid: true });
  });

  it('hashResult() é determinístico e sensível ao conteúdo', () => {
    const a = hashResult({ content: [{ type: 'text', text: 'ok' }] });
    const b = hashResult({ content: [{ type: 'text', text: 'ok' }] });
    const c = hashResult({ content: [{ type: 'text', text: 'outro' }] });
    expect(a).toBe(b);
    expect(a).not.toBe(c);
  });
});
