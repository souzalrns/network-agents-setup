import Redis from 'ioredis';
export class RedisCache {
  private client: Redis;
  constructor(url: string, private defaultTTL: number = 3600) {
    this.client = new Redis(url);
  }
  async get<T>(key: string): Promise<T | null> {
    const data = await this.client.get(key);
    if (!data) return null;
    try { return JSON.parse(data); } catch { return data as any; }
  }
  async set(key: string, value: any, ttl?: number): Promise<void> {
    const data = typeof value === 'string' ? value : JSON.stringify(value);
    await this.client.set(key, data, 'EX', ttl || this.defaultTTL);
  }
  async delete(key: string): Promise<void> {
    await this.client.del(key);
  }
  async exists(key: string): Promise<boolean> {
    const result = await this.client.exists(key);
    return result === 1;
  }
  async keys(pattern: string): Promise<string[]> {
    return this.client.keys(pattern);
  }
  async clear(pattern: string): Promise<void> {
    const keys = await this.keys(pattern);
    if (keys.length > 0) {
      await this.client.del(...keys);
    }
  }
  async disconnect(): Promise<void> {
    await this.client.quit();
  }
}
