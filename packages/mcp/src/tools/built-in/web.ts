import * as cheerio from 'cheerio';
import { fetch as undiciFetch } from 'undici';
import { MCPTool } from '../ToolRegistry';
import { createSsrfSafeDispatcher } from './SsrfGuard';
import { toClientError } from '../../util/sanitizeError';

const ALLOWED_SCHEMES = new Set(['http:', 'https:']);
const REQUEST_TIMEOUT_MS = 5000;

// Categorias de erro seguras e deliberadas (A5) -- ja nao expoem detalhe
// tecnico nenhum (nao sao "raw" error.message), por isso o A18 nao as
// generaliza mais: sao a mensagem certa a mostrar, nao um leak a esconder.
class SchemeNotAllowedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SchemeNotAllowedError';
  }
}
class RedirectBlockedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'RedirectBlockedError';
  }
}

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
          const parsed = new URL(url);
          if (!ALLOWED_SCHEMES.has(parsed.protocol)) {
            throw new SchemeNotAllowedError(`Scheme not allowed: ${parsed.protocol} (only http:/https:)`);
          }

          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
          let response;
          try {
            response = await undiciFetch(url, {
              method,
              headers: { 'Content-Type': 'application/json', ...headers },
              body: body || undefined,
              redirect: 'manual',
              dispatcher: createSsrfSafeDispatcher(),
              signal: controller.signal,
            });
          } finally {
            clearTimeout(timeoutId);
          }

          if (response.status >= 300 && response.status < 400) {
            throw new RedirectBlockedError(
              `Redirect blocked: ${response.status} to "${response.headers.get('location') || 'unknown'}" (redirects can point to internal targets)`
            );
          }

          const contentType = response.headers.get('content-type') || '';
          const data = contentType.includes('application/json') ? await response.json() : await response.text();
          return {
            content: [{ type: 'text', text: JSON.stringify({ status: response.status, data }, null, 2) }],
            metadata: { status: response.status, ok: response.ok },
          };
        } catch (error: any) {
          // O undici embrulha erros de ligacao (incluindo os da guarda de
          // SSRF, lancados dentro do `connect` do dispatcher) num
          // `TypeError('fetch failed', {cause})` generico -- a mensagem
          // especifica fica em `error.cause`, confirmado empiricamente.
          // As 3 categorias abaixo (timeout, esquema, redirect -- e a
          // guarda de SSRF, via error.cause) sao mensagens seguras e
          // deliberadas do A5, nao "raw" error.message -- o A18 só
          // generaliza o fallback verdadeiramente desconhecido.
          let message: string;
          if (error.name === 'AbortError') {
            message = `Timeout after ${REQUEST_TIMEOUT_MS}ms`;
          } else if (
            error.name === 'SchemeNotAllowedError' ||
            error.name === 'RedirectBlockedError' ||
            error.cause?.name === 'SsrfBlockedError'
          ) {
            message = error.cause?.message || error.message;
          } else {
            message = toClientError(error, 'ao fazer pedido HTTP');
          }
          return { content: [{ type: 'text', text: `HTTP error: ${message}` }], isError: true };
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
          const $ = cheerio.load(html);
          const result: any = { url, title: $('title').text() || 'No title', contentLength: html.length };
          if (selector) {
            const matches = $(selector)
              .map((_, el) => $(el).text())
              .get();
            result.matches = matches;
          }
          return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: 'text', text: toClientError(error, 'ao processar página web') }], isError: true };
        }
      },
    },
  ];
}
