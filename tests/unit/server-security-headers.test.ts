import { describe, it, expect, afterEach } from 'vitest';
import http from 'http';
import { createServer } from '../../apps/api/src/server';

describe('createServer — security headers (A20)', () => {
  let server: http.Server | undefined;

  afterEach(() => {
    server?.close();
  });

  it('crossOriginResourcePolicy é "cross-origin", não o omissão "same-origin" do helmet', async () => {
    const app = createServer({} as any, {} as any, {} as any, {} as any);
    server = app.listen(0);
    const port = (server.address() as any).port;

    const headers = await new Promise<http.IncomingHttpHeaders>((resolve) => {
      http.get(`http://127.0.0.1:${port}/health`, (res) => {
        res.resume();
        resolve(res.headers);
      });
    });

    expect(headers['cross-origin-resource-policy']).toBe('cross-origin');
    // Os outros headers do helmet continuam presentes (não foram tocados).
    expect(headers['x-frame-options']).toBe('SAMEORIGIN');
    expect(headers['content-security-policy']).toContain("default-src 'self'");
    expect(headers['strict-transport-security']).toContain('max-age=');
  });
});
