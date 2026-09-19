import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { authorize, rateLimit, audit, hashParamsForAudit } from '../../packages/mcp/src/tools/ToolPolicy';

const ORIGINAL_ENV = { ...process.env };

describe('ToolPolicy — authorize (desenho inspirado em policy.py)', () => {
  beforeEach(() => {
    delete process.env.MCP_POLICY_PROFILE;
    delete process.env.MCP_POLICY_KEY;
    delete process.env.MCP_POLICY_ALLOW_MUTATE;
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it('omissao (sem MCP_POLICY_PROFILE) e strict — nega mutação sem key', () => {
    const result = authorize('agent-1', 'write_file');
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe('strict_requires_key');
    expect(result.profile).toBe('strict');
  });

  it('strict + key configurada → allowed, reason key_configured', () => {
    process.env.MCP_POLICY_PROFILE = 'strict';
    process.env.MCP_POLICY_KEY = 'secret123';
    const result = authorize('agent-1', 'write_file');
    expect(result.allowed).toBe(true);
    expect(result.reason).toBe('key_configured');
  });

  it('strict + key configurada mas providedKey errado → denied, reason invalid_key', () => {
    process.env.MCP_POLICY_PROFILE = 'strict';
    process.env.MCP_POLICY_KEY = 'secret123';
    const result = authorize('agent-1', 'write_file', 'wrong-key');
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe('invalid_key');
  });

  it('moderate + sem key + tool de mutação → allowed, reason moderate_lab_open', () => {
    process.env.MCP_POLICY_PROFILE = 'moderate';
    const result = authorize('agent-1', 'query_database');
    expect(result.allowed).toBe(true);
    expect(result.reason).toBe('moderate_lab_open');
  });

  it('MCP_POLICY_ALLOW_MUTATE=1 permite mutação mesmo sem key nem moderate', () => {
    process.env.MCP_POLICY_PROFILE = 'strict';
    process.env.MCP_POLICY_ALLOW_MUTATE = '1';
    const result = authorize('agent-1', 'write_file');
    expect(result.allowed).toBe(true);
    expect(result.reason).toBe('allow_mutate_env');
  });

  it('permissive → allowed sempre, mesmo para tool de mutação sem key', () => {
    process.env.MCP_POLICY_PROFILE = 'permissive';
    const result = authorize('agent-1', 'query_database');
    expect(result.allowed).toBe(true);
    expect(result.reason).toBe('permissive');
  });

  it('tool de leitura, qualquer perfil não-permissive → allowed, reason read_ok', () => {
    process.env.MCP_POLICY_PROFILE = 'strict';
    const result = authorize('agent-1', 'read_file');
    expect(result.allowed).toBe(true);
    expect(result.reason).toBe('read_ok');
  });

  it('tool desconhecida → denied, reason unknown_tool', () => {
    const result = authorize('agent-1', 'delete_universe');
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe('unknown_tool');
  });
});

describe('ToolPolicy — rateLimit', () => {
  it('permite ate ao limite, nega a chamada seguinte (61a) na mesma janela', () => {
    const caller = 'rl-caller-strict-limit';
    let last;
    for (let i = 0; i < 60; i++) {
      last = rateLimit(caller);
      expect(last.allowed).toBe(true);
    }
    expect(last!.remaining).toBe(0);
    const denied = rateLimit(caller);
    expect(denied.allowed).toBe(false);
    expect(denied.remaining).toBe(0);
    expect(denied.reset_in).toBeGreaterThanOrEqual(0);
  });

  it('callers diferentes tem contadores independentes', () => {
    const callerA = 'rl-caller-a';
    const callerB = 'rl-caller-b';
    for (let i = 0; i < 60; i++) {
      expect(rateLimit(callerA).allowed).toBe(true);
    }
    expect(rateLimit(callerA).allowed).toBe(false);
    // callerB nunca chamou -- deve continuar livre
    expect(rateLimit(callerB).allowed).toBe(true);
  });
});

describe('ToolPolicy — audit', () => {
  let tmpDir: string;
  let logPath: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'toolpolicy-audit-'));
    logPath = path.join(tmpDir, 'audit.jsonl');
    process.env.MCP_AUDIT_LOG_PATH = logPath;
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('escreve 1 evento em JSONL e o formato bate com o esperado', () => {
    audit({
      caller: 'agent-1',
      tool: 'write_file',
      params_hash: hashParamsForAudit({ path: 'x.txt' }),
      allowed: true,
      reason: 'key_configured',
    });

    const content = fs.readFileSync(logPath, 'utf-8').trim();
    const lines = content.split('\n');
    expect(lines.length).toBe(1);

    const event = JSON.parse(lines[0]);
    expect(event.caller).toBe('agent-1');
    expect(event.tool).toBe('write_file');
    expect(event.allowed).toBe(true);
    expect(event.reason).toBe('key_configured');
    expect(typeof event.params_hash).toBe('string');
    expect(typeof event.at).toBe('string');
    expect(() => new Date(event.at).toISOString()).not.toThrow();
  });

  it('é append-only — 2 eventos ficam em 2 linhas, nenhuma apagada', () => {
    audit({ caller: 'a', tool: 'read_file', params_hash: 'h1', allowed: true, reason: 'read_ok' });
    audit({ caller: 'b', tool: 'write_file', params_hash: 'h2', allowed: false, reason: 'strict_requires_key' });
    const lines = fs.readFileSync(logPath, 'utf-8').trim().split('\n');
    expect(lines.length).toBe(2);
    expect(JSON.parse(lines[0]).caller).toBe('a');
    expect(JSON.parse(lines[1]).caller).toBe('b');
  });
});
