import { MCPTool } from '../ToolRegistry';
import fs from 'fs/promises';
import path from 'path';
export function createFilesystemTools(basePath: string): MCPTool[] {
  const safePath = (filePath: string): string => {
    const resolved = path.resolve(basePath, filePath);
    if (!resolved.startsWith(basePath)) throw new Error(`Access denied: ${filePath}`);
    return resolved;
  };
  return [
    {
      name: 'read_file',
      description: 'Read the content of a file',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string', description: 'Path to the file' },
          encoding: { type: 'string', description: 'File encoding', default: 'utf-8' },
        },
        required: ['path'],
      },
      execute: async ({ path: filePath, encoding = 'utf-8' }) => {
        try {
          const content = await fs.readFile(safePath(filePath), encoding as BufferEncoding);
          return { content: [{ type: 'text', text: content }], metadata: { size: content.length } };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Error: ${error.message}` }], isError: true };
        }
      },
    },
    {
      name: 'write_file',
      description: 'Write content to a file',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string', description: 'Path to the file' },
          content: { type: 'string', description: 'Content to write' },
          encoding: { type: 'string', description: 'File encoding', default: 'utf-8' },
        },
        required: ['path', 'content'],
      },
      execute: async ({ path: filePath, content, encoding = 'utf-8' }) => {
        try {
          const fullPath = safePath(filePath);
          await fs.mkdir(path.dirname(fullPath), { recursive: true });
          await fs.writeFile(fullPath, content, encoding as BufferEncoding);
          return { content: [{ type: 'text', text: `File written: ${filePath}` }] };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Error: ${error.message}` }], isError: true };
        }
      },
    },
    {
      name: 'list_directory',
      description: 'List the contents of a directory',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string', description: 'Path to the directory', default: '.' },
          recursive: { type: 'boolean', description: 'List recursively', default: false },
        },
      },
      execute: async ({ path: dirPath = '.', recursive = false }) => {
        try {
          const fullPath = safePath(dirPath);
          const entries: any[] = [];
          const list = async (dir: string, prefix = '') => {
            const items = await fs.readdir(dir);
            for (const item of items) {
              const fullItem = path.join(dir, item);
              const stat = await fs.stat(fullItem);
              entries.push({ name: path.join(prefix, item), isDirectory: stat.isDirectory(), size: stat.size });
              if (recursive && stat.isDirectory()) await list(fullItem, path.join(prefix, item));
            }
          };
          await list(fullPath);
          return { content: [{ type: 'text', text: JSON.stringify(entries, null, 2) }], metadata: { count: entries.length } };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Error: ${error.message}` }], isError: true };
        }
      },
    },
  ];
}
