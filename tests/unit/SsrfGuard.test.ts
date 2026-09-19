import { describe, it, expect } from 'vitest';
import { isBlockedIp } from '../../packages/mcp/src/tools/built-in/SsrfGuard';

describe('SsrfGuard — isBlockedIp (classificação de IP pós-resolução)', () => {
  it('IP unicast público (ex. 200.0.x.x) é permitido', () => {
    expect(isBlockedIp('200.0.1.1')).toBe(false);
    expect(isBlockedIp('8.8.8.8')).toBe(false);
  });

  it('127.0.0.1 (loopback IPv4) é bloqueado', () => {
    expect(isBlockedIp('127.0.0.1')).toBe(true);
  });

  it('::1 (loopback IPv6) é bloqueado', () => {
    expect(isBlockedIp('::1')).toBe(true);
  });

  it('169.254.169.254 (metadata endpoint cloud) é bloqueado', () => {
    expect(isBlockedIp('169.254.169.254')).toBe(true);
  });

  it('10.x.x.x (RFC1918) é bloqueado', () => {
    expect(isBlockedIp('10.0.0.5')).toBe(true);
  });

  it('192.168.x.x (RFC1918) é bloqueado', () => {
    expect(isBlockedIp('192.168.1.1')).toBe(true);
  });

  it('172.16-31.x.x (RFC1918) é bloqueado', () => {
    expect(isBlockedIp('172.16.0.1')).toBe(true);
    expect(isBlockedIp('172.31.255.255')).toBe(true);
    // fora do intervalo 172.16-31 -- nao e RFC1918, deve ser permitido
    expect(isBlockedIp('172.32.0.1')).toBe(false);
  });

  it('fe80::/10 (link-local IPv6) é bloqueado', () => {
    expect(isBlockedIp('fe80::1')).toBe(true);
  });

  it('::ffff:127.0.0.1 (loopback IPv4-mapeado-em-IPv6) é bloqueado', () => {
    expect(isBlockedIp('::ffff:127.0.0.1')).toBe(true);
  });

  it('IP inválido/não-parseável é bloqueado (fail-closed)', () => {
    expect(isBlockedIp('not-an-ip')).toBe(true);
    expect(isBlockedIp('')).toBe(true);
  });
});
