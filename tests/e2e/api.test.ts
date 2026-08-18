import { describe, it, expect } from 'vitest';
import request from 'supertest';
describe('API E2E', () => {
  it('should return health status', async () => {
    const response = await request('http://localhost:3000')
      .get('/health')
      .expect(200);
    expect(response.body).toHaveProperty('status', 'healthy');
    expect(response.body).toHaveProperty('version');
  });
  it('should list agents', async () => {
    const response = await request('http://localhost:3000')
      .get('/agents')
      .expect(200);
    expect(Array.isArray(response.body)).toBe(true);
  });
  it('should reject chat without message', async () => {
    const response = await request('http://localhost:3000')
      .post('/chat')
      .send({})
      .expect(400);
    expect(response.body).toHaveProperty('error');
  });
});
