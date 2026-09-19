import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import { createFilesystemTools } from '../../packages/mcp/src/tools/built-in/filesystem';

describe('filesystem tools — guarda de path traversal', () => {
  let root: string;
  let base: string;

  beforeAll(async () => {
    root = await fs.mkdtemp(path.join(os.tmpdir(), 'fs-guard-'));
    base = path.join(root, 'app');
    const sibling = path.join(root, 'app-secret');
    await fs.mkdir(base, { recursive: true });
    await fs.mkdir(sibling, { recursive: true });
    await fs.writeFile(path.join(sibling, 'secret.txt'), 'top secret');
    await fs.writeFile(path.join(base, 'readme.md'), 'hello');
  });

  afterAll(async () => {
    await fs.rm(root, { recursive: true, force: true });
  });

  it('bloqueia acesso a directório irmão que só partilha o prefixo (bug real, guarda sem separador)', async () => {
    const tools = createFilesystemTools(base);
    const readFile = tools.find((t) => t.name === 'read_file')!;
    const result: any = await readFile.execute({ path: '../app-secret/secret.txt' });
    expect(result.isError).toBe(true);
  });

  it('não-regressão: caminho válido dentro da base continua a resolver', async () => {
    const tools = createFilesystemTools(base);
    const readFile = tools.find((t) => t.name === 'read_file')!;
    const result: any = await readFile.execute({ path: 'readme.md' });
    expect(result.isError).toBeUndefined();
    expect(result.content[0].text).toBe('hello');
  });
});
