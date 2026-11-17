import { promises as dns } from "node:dns";
import { BlockList, isIP } from "node:net";
import defaultAllowlist from "../../../config/radar-allowlist.json";

/**
 * Pedido seguro a um feed. Regras (todas verificadas em cada salto de redireccionamento):
 * - só HTTPS, porta 443, sem credenciais no endereço;
 * - o anfitrião tem de estar na lista de domínios permitidos (um domínio permite os seus subdomínios);
 * - recusa IP literal, `localhost` e nomes cujo DNS aponte para endereços privados, de loopback ou link-local (SSRF);
 * - 15 s no total, 2 MB de corpo no máximo, 3 redireccionamentos no máximo;
 * - pedido condicional (ETag / Last-Modified): 304 é «sem alterações»;
 * - 401, 403 e 451 marcam a fonte como bloqueada: não se contorna autenticação, paywall nem bloqueio.
 */

export const USER_AGENT = "EditorialRadar/0.1 (+https://example.invalid/radar)";
export const DEFAULT_TIMEOUT_MS = 15_000;
export const DEFAULT_MAX_BYTES = 2 * 1024 * 1024;
export const DEFAULT_MAX_REDIRECTS = 3;
export const DEFAULT_ALLOWLIST: readonly string[] = (defaultAllowlist as string[]).map(normaliseDomain).filter(Boolean);

export type FetchImpl = (url: string, init: RequestInit) => Promise<Response>;
export type Resolver = (host: string) => Promise<string[]>;

export interface SafeFetchOpts {
  allowlist?: readonly string[];
  fetchImpl?: FetchImpl;
  resolve?: Resolver;
  etag?: string | null;
  lastModified?: string | null;
  timeoutMs?: number;
  maxBytes?: number;
  maxRedirects?: number;
}

export type FetchReason =
  | "invalid_url" | "not_https" | "credentials" | "port" | "ip_literal" | "localhost" | "not_allowed"
  | "dns" | "private_address" | "too_many_redirects" | "bad_redirect" | "timeout" | "too_large"
  | "http_error" | "network";

export type FetchOutcome =
  | { kind: "ok"; status: number; url: string; body: string; contentType: string; etag: string | null; lastModified: string | null }
  | { kind: "not_modified"; status: 304; url: string; etag: string | null; lastModified: string | null }
  | { kind: "blocked"; status: number; url: string; message: string }
  | { kind: "error"; status?: number; url: string; reason: FetchReason; message: string };

export type UrlCheck = { ok: true; url: URL; host: string } | { ok: false; reason: FetchReason; message: string };

function normaliseDomain(d: string): string {
  return String(d).trim().toLowerCase().replace(/^\*\./, "").replace(/^\.+|\.+$/g, "");
}

/** O anfitrião é o domínio ou um subdomínio dele (`uc.pt` permite `noticias.uc.pt`, não `fakeuc.pt`). */
export function hostAllowed(host: string, allowlist: readonly string[]): boolean {
  const h = host.toLowerCase().replace(/\.+$/, "");
  return allowlist.some((raw) => {
    const d = normaliseDomain(raw);
    return d !== "" && (h === d || h.endsWith(`.${d}`));
  });
}

/** Verificação sem rede: esquema, porta, credenciais, IP literal, localhost e lista de domínios. */
export function checkUrl(raw: string, allowlist: readonly string[] = DEFAULT_ALLOWLIST): UrlCheck {
  let url: URL;
  try { url = new URL(raw); } catch { return { ok: false, reason: "invalid_url", message: "Endereço inválido." }; }
  if (url.protocol !== "https:") return { ok: false, reason: "not_https", message: "Só se aceitam feeds em HTTPS." };
  if (url.username || url.password) return { ok: false, reason: "credentials", message: "O endereço não pode levar credenciais." };
  if (url.port && url.port !== "443") return { ok: false, reason: "port", message: "Só se aceita a porta 443." };
  const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, "").replace(/\.+$/, "");
  if (isIP(host)) return { ok: false, reason: "ip_literal", message: "Não se aceitam endereços IP, só nomes de domínio." };
  if (host === "localhost" || host.endsWith(".localhost") || !host.includes(".")) {
    return { ok: false, reason: "localhost", message: "Anfitrião local recusado." };
  }
  if (!hostAllowed(host, allowlist)) {
    return { ok: false, reason: "not_allowed", message: `O domínio ${host} não está na lista de fontes permitidas.` };
  }
  return { ok: true, url, host };
}

// ---------------------------------------------------------------- endereços que não são da Internet pública
const blocked = new BlockList();
for (const [net, prefix] of [
  ["0.0.0.0", 8], ["10.0.0.0", 8], ["100.64.0.0", 10], ["127.0.0.0", 8], ["169.254.0.0", 16], ["172.16.0.0", 12],
  ["192.0.0.0", 24], ["192.0.2.0", 24], ["192.88.99.0", 24], ["192.168.0.0", 16], ["198.18.0.0", 15],
  ["198.51.100.0", 24], ["203.0.113.0", 24], ["224.0.0.0", 4], ["240.0.0.0", 4],
] as const) blocked.addSubnet(net, prefix, "ipv4");
for (const [net, prefix] of [
  ["::", 128], ["::1", 128], ["::", 96], ["64:ff9b::", 96], ["64:ff9b:1::", 48], ["100::", 64], ["2001::", 32],
  ["2001:db8::", 32], ["2002::", 16], ["fc00::", 7], ["fe80::", 10], ["fec0::", 10], ["ff00::", 8],
] as const) blocked.addSubnet(net, prefix, "ipv6");

/** IPv4 embutido num IPv6 mapeado (`::ffff:a.b.c.d` ou `::ffff:7f00:1`). */
function mappedV4(ip: string): string | null {
  const m = /^(?:0{0,4}:){0,5}:?ffff:(.+)$/i.exec(ip);
  if (!m) return null;
  const rest = m[1]!;
  if (isIP(rest) === 4) return rest;
  const hex = /^([0-9a-f]{1,4}):([0-9a-f]{1,4})$/i.exec(rest);
  if (!hex) return null;
  const hi = parseInt(hex[1]!, 16), lo = parseInt(hex[2]!, 16);
  return `${hi >> 8}.${hi & 255}.${lo >> 8}.${lo & 255}`;
}

export function isPublicAddress(ip: string): boolean {
  const addr = ip.replace(/^\[|\]$/g, "").split("%")[0]!;
  const v = isIP(addr);
  if (v === 4) return !blocked.check(addr, "ipv4");
  if (v === 6) {
    const v4 = mappedV4(addr);
    if (v4) return !blocked.check(v4, "ipv4");
    return !blocked.check(addr, "ipv6");
  }
  return false;
}

export const systemResolver: Resolver = async (host) =>
  (await dns.lookup(host, { all: true, verbatim: true })).map((a) => a.address);

/** Verificação completa de um endereço, incluindo o DNS (todos os endereços têm de ser públicos). */
export async function checkTarget(raw: string, allowlist: readonly string[], resolve: Resolver): Promise<UrlCheck> {
  const c = checkUrl(raw, allowlist);
  if (!c.ok) return c;
  let addrs: string[];
  try { addrs = await resolve(c.host); } catch { return { ok: false, reason: "dns", message: `Não foi possível resolver ${c.host}.` }; }
  if (!addrs.length) return { ok: false, reason: "dns", message: `${c.host} não tem endereços.` };
  if (addrs.some((a) => !isPublicAddress(a))) {
    return { ok: false, reason: "private_address", message: `${c.host} aponta para um endereço privado ou local: recusado.` };
  }
  return c;
}

// ---------------------------------------------------------------- corpo com limite e decodificação
class TooLarge extends Error {}

async function readLimited(res: Response, max: number): Promise<Uint8Array> {
  const declared = Number(res.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > max) { await res.body?.cancel().catch(() => {}); throw new TooLarge(); }
  if (!res.body) {
    const buf = new Uint8Array(await res.arrayBuffer());
    if (buf.byteLength > max) throw new TooLarge();
    return buf;
  }
  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > max) { await reader.cancel().catch(() => {}); throw new TooLarge(); }
    chunks.push(value);
  }
  const out = new Uint8Array(total);
  let off = 0;
  for (const c of chunks) { out.set(c, off); off += c.byteLength; }
  return out;
}

/** Codificação pelo cabeçalho, senão pela declaração XML; por omissão UTF-8. Há feeds portugueses em ISO-8859-1. */
function decode(bytes: Uint8Array, contentType: string): string {
  const fromHeader = /charset=["']?([\w.:-]+)/i.exec(contentType)?.[1];
  const head = new TextDecoder("latin1").decode(bytes.subarray(0, 256));
  const fromXml = /^\s*<\?xml[^>]*encoding=["']([\w.:-]+)["']/i.exec(head)?.[1];
  for (const label of [fromHeader, fromXml, "utf-8"]) {
    if (!label) continue;
    try { return new TextDecoder(label).decode(bytes); } catch { /* codificação desconhecida: tenta a seguinte */ }
  }
  return new TextDecoder().decode(bytes);
}

const REDIRECTS = new Set([301, 302, 303, 307, 308]);
const BLOCKING = new Set([401, 403, 451]);

/** Pede um feed respeitando as regras acima. Nunca lança por falhas esperadas: devolve o resultado. */
export async function safeFetch(rawUrl: string, opts: SafeFetchOpts = {}): Promise<FetchOutcome> {
  const allowlist = opts.allowlist ?? DEFAULT_ALLOWLIST;
  const fetchImpl: FetchImpl = opts.fetchImpl ?? ((u, init) => fetch(u, init));
  const resolve = opts.resolve ?? systemResolver;
  const maxBytes = opts.maxBytes ?? DEFAULT_MAX_BYTES;
  const maxRedirects = opts.maxRedirects ?? DEFAULT_MAX_REDIRECTS;
  const timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<FetchOutcome>((done) => {
    timer = setTimeout(() => {
      controller.abort();
      done({ kind: "error", url: rawUrl, reason: "timeout", message: `Sem resposta em ${Math.round(timeoutMs / 1000)} s.` });
    }, timeoutMs);
  });

  const run = async (): Promise<FetchOutcome> => {
    let current = rawUrl;
    for (let hop = 0; ; hop++) {
      const check = await checkTarget(current, allowlist, resolve);
      if (!check.ok) return { kind: "error", url: current, reason: check.reason, message: check.message };

      const headers: Record<string, string> = {
        "user-agent": USER_AGENT,
        accept: "application/rss+xml, application/atom+xml, application/rdf+xml;q=0.9, application/xml;q=0.8, text/xml;q=0.8, */*;q=0.1",
      };
      if (opts.etag) headers["if-none-match"] = opts.etag;
      if (opts.lastModified) headers["if-modified-since"] = opts.lastModified;

      let res: Response;
      try {
        res = await fetchImpl(check.url.toString(), { method: "GET", headers, redirect: "manual", signal: controller.signal });
      } catch (e) {
        if (controller.signal.aborted) throw e; // o temporizador já respondeu
        return { kind: "error", url: current, reason: "network", message: `Falha de rede: ${(e as Error).message}`.slice(0, 300) };
      }

      if (REDIRECTS.has(res.status)) {
        await res.body?.cancel().catch(() => {});
        const location = res.headers.get("location");
        if (!location) return { kind: "error", status: res.status, url: current, reason: "bad_redirect", message: "Redireccionamento sem destino." };
        if (hop >= maxRedirects) {
          return { kind: "error", status: res.status, url: current, reason: "too_many_redirects", message: `Mais de ${maxRedirects} redireccionamentos.` };
        }
        try { current = new URL(location, current).toString(); } catch {
          return { kind: "error", status: res.status, url: current, reason: "bad_redirect", message: "Destino de redireccionamento inválido." };
        }
        continue;
      }

      const etag = res.headers.get("etag");
      const lastModified = res.headers.get("last-modified");
      if (res.status === 304) {
        await res.body?.cancel().catch(() => {});
        return { kind: "not_modified", status: 304, url: current, etag: etag ?? opts.etag ?? null, lastModified: lastModified ?? opts.lastModified ?? null };
      }
      if (BLOCKING.has(res.status)) {
        await res.body?.cancel().catch(() => {});
        return { kind: "blocked", status: res.status, url: current,
          message: `A fonte recusou o acesso (HTTP ${res.status}); não se contorna: rever a fonte manualmente.` };
      }
      if (res.status < 200 || res.status >= 300) {
        await res.body?.cancel().catch(() => {});
        return { kind: "error", status: res.status, url: current, reason: "http_error", message: `A fonte respondeu HTTP ${res.status}.` };
      }

      const contentType = res.headers.get("content-type") ?? "";
      try {
        const bytes = await readLimited(res, maxBytes);
        return { kind: "ok", status: res.status, url: current, body: decode(bytes, contentType), contentType, etag, lastModified };
      } catch (e) {
        if (e instanceof TooLarge) {
          return { kind: "error", status: res.status, url: current, reason: "too_large", message: `O feed tem mais de ${Math.round(maxBytes / 1024)} KB.` };
        }
        if (controller.signal.aborted) throw e;
        return { kind: "error", status: res.status, url: current, reason: "network", message: `Falha ao ler o feed: ${(e as Error).message}`.slice(0, 300) };
      }
    }
  };

  try {
    return await Promise.race([run().catch(async (e) => {
      if (controller.signal.aborted) return timeout;
      throw e;
    }), timeout]);
  } finally {
    clearTimeout(timer);
  }
}
