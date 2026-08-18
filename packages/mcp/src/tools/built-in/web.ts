import { MCPTool } from '../ToolRegistry';
export function createWebTools(): MCPTool[] {
  return [
    {
      name: 'http_request',
      description: 'Make an HTTP request to a URL',
      inputSchema: {
        type: 'object',
        properties: {
          url: { type: 'string', description: 'URL to request' },
          method: { type: 'string', description: 'HTTP method', enum: ['GET', 'POST', 'PUT', 'DELETE'], default: 'GET' },
          headers: { type: 'object', description: 'HTTP headers', default: {} },
          body: { type: 'string', description: 'Request body' },
        },
        required: ['url'],
      },
      execute: async ({ url, method = 'GET', headers = {}, body }) => {
        try {
          const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json', ...headers },
            body: body || undefined,
          });
          const contentType = response.headers.get('content-type') || '';
          const data = contentType.includes('application/json') ? await response.json() : await response.text();
          return {
            content: [{ type: 'text', text: JSON.stringify({ status: response.status, data }, null, 2) }],
            metadata: { status: response.status, ok: response.ok },
          };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `HTTP error: ${error.message}` }], isError: true };
        }
      },
    },
    {
      name: 'scrape_webpage',
      description: 'Scrape and extract content from a webpage',
      inputSchema: {
        type: 'object',
        properties: {
          url: { type: 'string', description: 'URL of the webpage' },
          selector: { type: 'string', description: 'CSS selector to extract (optional)' },
        },
        required: ['url'],
      },
      execute: async ({ url, selector }) => {
        try {
          const response = await fetch(url, { headers: { 'User-Agent': 'MCP-Agent/1.0' } });
          const html = await response.text();
          const result: any = { url, title: html.match(/<title>(.*?)<\/title>/)?.[1] || 'No title', contentLength: html.length };
          if (selector) {
            const matches = html.match(new RegExp(`<${selector}>(.*?)</${selector}>`, 'gs'));
            result.matches = matches || [];
          }
          return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Scraping error: ${error.message}` }], isError: true };
        }
      },
    },
  ];
}
