import net from 'net';
import dns from 'dns';
import ipaddr from 'ipaddr.js';
import { Agent, buildConnector } from 'undici';

/**
 * Guarda de SSRF para o `fetch` do `undici` (o `fetch` global do Node NAO
 * aceita `agent`, so `dispatcher` -- ver nota no web.ts / EXECUTION-PROMPTS A5).
 *
 * Nao usa `ssrf-req-filter`: essa lib devolve um `http.Agent` classico,
 * incompativel com o `dispatcher` do undici (confirmado empiricamente --
 * `agent.createConnection` nunca e chamado pelo fetch global). O principio
 * e o mesmo (validar o IP pos-resolucao DNS, nao a string do hostname),
 * mas a integracao tem de ser feita ao nivel do `connect` do undici.
 *
 * Fecha a janela de DNS-rebinding resolvendo o hostname uma unica vez aqui,
 * validando o IP resultante, e depois ligando directamente a esse IP
 * (mantendo o hostname original em `servername` para SNI/TLS correcto) --
 * nao deixa o connector por omissao re-resolver DNS uma segunda vez.
 */

const defaultConnect = buildConnector({});

export class SsrfBlockedError extends Error {
  constructor(host: string, resolvedIp?: string) {
    super(
      resolvedIp && resolvedIp !== host
        ? `SSRF bloqueado: "${host}" resolve para "${resolvedIp}", que nao e um endereco unicast publico`
        : `SSRF bloqueado: "${host}" nao e um endereco unicast publico`
    );
    this.name = 'SsrfBlockedError';
  }
}

/**
 * Classifica um IP. Ao contrario da lib ssrf-req-filter (que trata um IP
 * nao-parseavel como seguro), aqui um IP que nao se consiga interpretar e
 * tratado como BLOQUEADO -- fail-closed, consistente com o resto desta
 * sessao (perfil "strict" por omissao no ToolPolicy, etc.).
 */
export function isBlockedIp(ip: string): boolean {
  if (!ipaddr.isValid(ip)) {
    return true;
  }
  try {
    const addr = ipaddr.parse(ip);
    const range = addr.range();
    return range !== 'unicast';
  } catch {
    return true;
  }
}

function ssrfSafeConnect(
  options: buildConnector.Options,
  callback: buildConnector.Callback
): void {
  const host = options.hostname;

  if (net.isIP(host)) {
    if (isBlockedIp(host)) {
      callback(new SsrfBlockedError(host), null as any);
      return;
    }
    defaultConnect(options, callback);
    return;
  }

  dns.lookup(host, (err, address) => {
    if (err) {
      callback(err, null as any);
      return;
    }
    if (isBlockedIp(address)) {
      callback(new SsrfBlockedError(host, address), null as any);
      return;
    }
    const safeOptions: buildConnector.Options = {
      ...options,
      hostname: address,
      servername: options.servername || host,
    };
    defaultConnect(safeOptions, callback);
  });
}

/**
 * Devolve um `undici.Agent` (dispatcher) que valida o IP pos-DNS antes de
 * ligar. Uso: `fetch(url, { dispatcher: createSsrfSafeDispatcher() })`.
 */
export function createSsrfSafeDispatcher(): Agent {
  return new Agent({ connect: ssrfSafeConnect });
}
