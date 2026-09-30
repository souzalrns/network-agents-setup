import { describe, it, expect } from 'vitest';
import request from 'supertest';
// Precisa da API a correr (não é arrancada aqui; o CI não corre tests/e2e, ci.yml:93).
// E2E_BASE_URL: omissão http://localhost:3000. E2E_API_KEY: enviada como x-api-key,
// obrigatória quando a API tem API_KEY (auth fail-closed, apps/api/src/middleware/auth.ts).
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
const HEADERS: Record<string, string> = process.env.E2E_API_KEY
  ? { 'x-api-key': process.env.E2E_API_KEY }
  : {};
describe('API E2E', () => {
  it('should return health status', async () => {
    const response = await request(BASE_URL)
      .get('/health')
      .set(HEADERS)
      .expect(200);
    expect(response.body).toHaveProperty('status', 'healthy');
    expect(response.body).toHaveProperty('version');
  });
  it('should list agents', async () => {
    const response = await request(BASE_URL)
      .get('/agents')
      .set(HEADERS)
      .expect(200);
    expect(Array.isArray(response.body)).toBe(true);
  });
  it('should reject chat without message', async () => {
    const response = await request(BASE_URL)
      .post('/chat')
      .set(HEADERS)
      .send({})
      .expect(400);
    expect(response.body).toHaveProperty('error');
  });
});
