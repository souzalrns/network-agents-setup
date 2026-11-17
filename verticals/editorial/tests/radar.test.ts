import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { agentCtx, systemCtx } from "@/lib/context";
import { closeDb, withCtx } from "@/lib/db";
import {
  checkUrl, DEFAULT_ALLOWLIST, DEFAULT_TOPICS, dismissItem, type FetchImpl, FeedError, isPublicAddress, parseFeed,
  promoteToIdea, type Resolver, runRadar, runRadarAll, safeFetch, scoreItem, USER_AGENT,
} from "@/lib/radar";
import { EditorialError } from "@/lib/stories";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

// ---------------------------------------------------------------- rede simulada (os testes não saem para a Internet)
const ALLOW = ["radar-a.pt", "radar-b.pt", "instituicao.gov.pt"];
const publicDns: Resolver = async () => ["93.184.216.34"];

type Handler = (init: RequestInit) => Response | Promise<Response>;
function net(routes: Record<string, Handler>) {
  const calls: { url: string; headers: Record<string, string> }[] = [];
  const impl: FetchImpl = async (url, init) => {
    calls.push({ url, headers: { ...(init.headers as Record<string, string>) } });
    const h = routes[url];
    if (!h) return new Response("não existe", { status: 404 });
    return h(init);
  };
  return { impl, calls };
}
const xml = (body: string, headers: Record<string, string> = {}) => () =>
  new Response(body, { status: 200, headers: { "content-type": "application/rss+xml; charset=utf-8", ...headers } });

const hoje = new Date().toUTCString();
const rss = (items: string, title = "Feed de teste") =>
  `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
   <channel><title>${title}</title><link>https://radar-a.pt/</link>
   <atom:link href="https://radar-a.pt/feed" rel="self" type="application/rss+xml"/>${items}</channel></rss>`;
const item = (title: string, link: string, desc = "Resumo curto.") =>
  `<item><title><![CDATA[${title}]]></title><link>${link}</link><pubDate>${hoje}</pubDate><description><![CDATA[${desc}]]></description></item>`;

// ---------------------------------------------------------------- leitura de feeds
describe("leitura de RSS e Atom", () => {
  it("lê RSS 2.0 com CDATA, entidades, data, guid e ligações relativas", () => {
    const f = parseFeed(rss(`
      <item><title><![CDATA[Câmara de Coimbra aprova <b>orçamento</b>]]></title>
        <link>https://radar-a.pt/n/1?utm_source=rss</link><pubDate>Tue, 17 Nov 2026 10:00:00 +0000</pubDate>
        <description>&lt;p&gt;A assembleia &amp;amp; a vereação &amp;#8220;votaram&amp;#8221; &amp;eacute;&lt;/p&gt;</description></item>
      <item><title>Só com guid</title><guid isPermaLink="true">https://radar-a.pt/n/2</guid><dc:date>2026-11-16T09:00:00Z</dc:date></item>
      <item><title>Relativa</title><link>/n/3</link><pubDate>data inválida</pubDate></item>
      <item><title>Sem ligação</title><description>nada</description></item>
      <item><link>https://radar-a.pt/n/5</link><description>Sem título mas com texto útil.</description></item>
      <item><title>Javascript</title><link>javascript:alert(1)</link></item>`));
    expect(f.format).toBe("rss");
    expect(f.title).toBe("Feed de teste");
    expect(f.entries.map((e) => e.url)).toEqual([
      "https://radar-a.pt/n/1?utm_source=rss", "https://radar-a.pt/n/2", "https://radar-a.pt/n/3", "https://radar-a.pt/n/5"]);
    const [a, b, c, d] = f.entries;
    expect(a!.title).toBe("Câmara de Coimbra aprova orçamento");
    expect(a!.publishedAt?.toISOString()).toBe("2026-11-17T10:00:00.000Z");
    expect(a!.summaryHtml).toBe("A assembleia & a vereação “votaram” é");
    expect(b!.publishedAt?.toISOString()).toBe("2026-11-16T09:00:00.000Z");
    expect(c!.publishedAt).toBeNull();
    expect(d!.title).toBe("Sem título mas com texto útil.");
  });

  it("lê um feed com uma só entrada e um canal sem campos opcionais", () => {
    const f = parseFeed(`<rss version="2.0"><channel><item><title>Única</title><link>https://radar-a.pt/u</link></item></channel></rss>`);
    expect(f.entries).toHaveLength(1);
    expect(f.entries[0]).toMatchObject({ title: "Única", url: "https://radar-a.pt/u", publishedAt: null, summaryHtml: "" });
    expect(parseFeed(`<rss version="2.0"><channel><title>Vazio</title></channel></rss>`).entries).toEqual([]);
  });

  it("lê Atom: ligação alternate, conteúdo HTML e XHTML, uma só entrada", () => {
    const atom = `<?xml version="1.0" encoding="utf-8"?>
      <feed xmlns="http://www.w3.org/2005/Atom"><title type="text">Instituição</title>
        <entry><title type="html">Relatório &lt;em&gt;anual&lt;/em&gt; do INE</title>
          <link rel="self" href="https://instituicao.gov.pt/api/1"/><link rel="alternate" href="https://instituicao.gov.pt/r/1"/>
          <updated>2026-11-15T08:30:00Z</updated><published>2026-11-14T08:30:00Z</published>
          <content type="html">&lt;p&gt;O &lt;strong&gt;desemprego&lt;/strong&gt; desceu.&lt;/p&gt;</content></entry>
        <entry><title>XHTML</title><link href="/r/2"/><updated>2026-11-15T09:00:00Z</updated>
          <summary type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml"><p>Parágrafo <b>um</b>.</p></div></summary></entry>
      </feed>`;
    const f = parseFeed(atom, "https://instituicao.gov.pt/feed.atom");
    expect(f.format).toBe("atom");
    expect(f.title).toBe("Instituição");
    expect(f.entries[0]).toMatchObject({ title: "Relatório anual do INE", url: "https://instituicao.gov.pt/r/1", summaryHtml: "O desemprego desceu." });
    expect(f.entries[0]!.publishedAt?.toISOString()).toBe("2026-11-14T08:30:00.000Z");
    expect(f.entries[1]!.url).toBe("https://instituicao.gov.pt/r/2");
    expect(f.entries[1]!.summaryHtml).toMatch(/Parágrafo.*um|um.*Parágrafo/);
    const one = parseFeed(`<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Só</title><link href="https://radar-b.pt/x"/></entry></feed>`);
    expect(one.entries).toHaveLength(1);
  });

  it("lê RSS 1.0 (RDF)", () => {
    const f = parseFeed(`<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"
      xmlns:dc="http://purl.org/dc/elements/1.1/"><channel rdf:about="https://radar-b.pt/"><title>RDF</title></channel>
      <item rdf:about="https://radar-b.pt/1"><title>Primeira</title><link>https://radar-b.pt/1</link><dc:date>2026-11-10T00:00:00Z</dc:date></item>
      </rdf:RDF>`);
    expect(f.format).toBe("rdf");
    expect(f.entries[0]).toMatchObject({ title: "Primeira", url: "https://radar-b.pt/1" });
  });

  it("recusa o que não é feed: vazio, lixo, HTML, XML truncado e bombas de entidades", () => {
    expect(() => parseFeed("")).toThrow(FeedError);
    expect(() => parseFeed("isto não é xml {")).toThrow(FeedError);
    expect(() => parseFeed("<!doctype html><html><body><p>Página</p></body></html>")).toThrow(FeedError);
    expect(() => parseFeed(`<rss><channel><item><title>truncado`)).toThrow(FeedError);
    const bomb = `<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">${Array.from({ length: 40 }, (_, i) =>
      `<!ENTITY lol${i} "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">`).join("")}]><rss><channel><item><title>&lol39;</title>
      <link>https://radar-a.pt/b</link></item></channel></rss>`;
    expect(() => parseFeed(bomb)).toThrow(FeedError);
  });

  it("guarda só um excerto: nunca mais de 300 caracteres, mesmo com o artigo inteiro no feed", () => {
    const artigo = `<p>${"Parágrafo de um artigo completo com muitas palavras. ".repeat(400)}</p><script>alert(1)</script>`;
    const f = parseFeed(rss(item("Artigo inteiro no feed", "https://radar-a.pt/longo", artigo)
      + `<item><title>${"T".repeat(1000)}</title><link>https://radar-a.pt/t</link><content:encoded><![CDATA[${artigo}]]></content:encoded></item>`));
    for (const e of f.entries) {
      expect(e.summaryHtml.length).toBeLessThanOrEqual(300);
      expect(e.title.length).toBeLessThanOrEqual(300);
      expect(e.summaryHtml).not.toContain("<");
    }
    expect(f.entries[0]!.summaryHtml.endsWith("…")).toBe(true);
  });
});

// ---------------------------------------------------------------- pedido seguro
describe("pedido seguro aos feeds", () => {
  it("a lista de domínios por omissão vem de config/radar-allowlist.json", () => {
    expect(DEFAULT_ALLOWLIST.length).toBeGreaterThan(0);
    expect(DEFAULT_ALLOWLIST).toContain("uc.pt");
    expect(checkUrl("https://noticias.uc.pt/feed/").ok).toBe(true);
  });

  it("recusa anfitriões fora da lista, http://, IP literal, localhost, credenciais e outras portas", () => {
    const r = (u: string) => { const c = checkUrl(u, ALLOW); return c.ok ? "ok" : c.reason; };
    expect(r("https://radar-a.pt/feed")).toBe("ok");
    expect(r("https://noticias.radar-a.pt/feed")).toBe("ok"); // subdomínio
    expect(r("https://falso-radar-a.pt/feed")).toBe("not_allowed");
    expect(r("https://radar-a.pt.atacante.com/feed")).toBe("not_allowed");
    expect(r("https://exemplo.com/feed")).toBe("not_allowed");
    expect(r("http://radar-a.pt/feed")).toBe("not_https");
    expect(r("ftp://radar-a.pt/feed")).toBe("not_https");
    expect(r("https://127.0.0.1/feed")).toBe("ip_literal");
    expect(r("https://2130706433/feed")).toBe("ip_literal"); // 127.0.0.1 em decimal
    expect(r("https://[::1]/feed")).toBe("ip_literal");
    expect(r("https://localhost/feed")).toBe("localhost");
    expect(r("https://intranet/feed")).toBe("localhost");
    expect(r("https://user:pass@radar-a.pt/feed")).toBe("credentials");
    expect(r("https://radar-a.pt:8443/feed")).toBe("port");
    expect(r("não é url")).toBe("invalid_url");
  });

  it("classifica endereços privados, de loopback e link-local (incluindo IPv6 e IPv4 mapeado)", () => {
    for (const ip of ["10.1.2.3", "127.0.0.1", "169.254.169.254", "172.16.0.1", "192.168.1.1", "100.64.0.1", "0.0.0.0",
      "::1", "fe80::1", "fd00::1", "::ffff:127.0.0.1", "::ffff:a9fe:a9fe", "224.0.0.1"]) {
      expect(isPublicAddress(ip), ip).toBe(false);
    }
    for (const ip of ["93.184.216.34", "2606:4700::1111", "193.137.200.1"]) expect(isPublicAddress(ip), ip).toBe(true);
  });

  it("recusa um domínio permitido cujo DNS aponta para um endereço privado (SSRF), sem fazer o pedido", async () => {
    const { impl, calls } = net({ "https://radar-a.pt/feed": xml(rss("")) });
    for (const addrs of [["10.0.0.5"], ["93.184.216.34", "169.254.169.254"], ["::1"]]) {
      const res = await safeFetch("https://radar-a.pt/feed", { allowlist: ALLOW, fetchImpl: impl, resolve: async () => addrs });
      expect(res).toMatchObject({ kind: "error", reason: "private_address" });
    }
    const falhaDns = await safeFetch("https://radar-a.pt/feed", { allowlist: ALLOW, fetchImpl: impl, resolve: async () => { throw new Error("NXDOMAIN"); } });
    expect(falhaDns).toMatchObject({ kind: "error", reason: "dns" });
    expect(calls).toHaveLength(0);
  });

  it("segue até 3 redireccionamentos e verifica cada destino contra a lista", async () => {
    const redirect = (to: string) => () => new Response(null, { status: 301, headers: { location: to } });
    const { impl, calls } = net({
      "https://radar-a.pt/feed": redirect("/feed2"),
      "https://radar-a.pt/feed2": redirect("https://radar-b.pt/feed"),
      "https://radar-b.pt/feed": xml(rss(item("Ok", "https://radar-b.pt/1"))),
      "https://radar-a.pt/fora": redirect("https://atacante.com/feed"),
      "https://radar-a.pt/http": redirect("http://radar-a.pt/feed"),
      "https://radar-a.pt/interno": redirect("https://interno.radar-a.pt/feed"),
      "https://radar-a.pt/r0": redirect("https://radar-a.pt/r1"),
      "https://radar-a.pt/r1": redirect("https://radar-a.pt/r2"),
      "https://radar-a.pt/r2": redirect("https://radar-a.pt/r3"),
      "https://radar-a.pt/r3": redirect("https://radar-a.pt/r4"),
    });
    const ok = await safeFetch("https://radar-a.pt/feed", { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    expect(ok).toMatchObject({ kind: "ok", url: "https://radar-b.pt/feed" });
    expect(await safeFetch("https://radar-a.pt/fora", { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns }))
      .toMatchObject({ kind: "error", reason: "not_allowed", url: "https://atacante.com/feed" });
    expect(await safeFetch("https://radar-a.pt/http", { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns }))
      .toMatchObject({ kind: "error", reason: "not_https" });
    const rebind: Resolver = async (h) => (h === "interno.radar-a.pt" ? ["192.168.0.10"] : ["93.184.216.34"]);
    expect(await safeFetch("https://radar-a.pt/interno", { allowlist: ALLOW, fetchImpl: impl, resolve: rebind }))
      .toMatchObject({ kind: "error", reason: "private_address" });
    expect(await safeFetch("https://radar-a.pt/r0", { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns }))
      .toMatchObject({ kind: "error", reason: "too_many_redirects" });
    expect(calls.some((c) => c.url.includes("atacante.com") || c.url.startsWith("http:") || c.url.includes("interno."))).toBe(false);
    expect(calls.every((c) => c.headers["user-agent"] === USER_AGENT)).toBe(true);
    expect(USER_AGENT).toBe("EditorialRadar/0.1 (+https://example.invalid/radar)");
  });

  it("pedido condicional: envia ETag e Last-Modified e trata 304 como «sem alterações»", async () => {
    const { impl, calls } = net({
      "https://radar-a.pt/feed": (init) => {
        const h = init.headers as Record<string, string>;
        return h["if-none-match"] === '"v1"' ? new Response(null, { status: 304 }) : new Response(rss(""), { status: 200, headers: { etag: '"v1"' } });
      },
    });
    const first = await safeFetch("https://radar-a.pt/feed", { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    expect(first).toMatchObject({ kind: "ok", etag: '"v1"' });
    const again = await safeFetch("https://radar-a.pt/feed", {
      allowlist: ALLOW, fetchImpl: impl, resolve: publicDns, etag: '"v1"', lastModified: "Mon, 16 Nov 2026 10:00:00 GMT" });
    expect(again).toMatchObject({ kind: "not_modified", etag: '"v1"', lastModified: "Mon, 16 Nov 2026 10:00:00 GMT" });
    expect(calls[1]!.headers).toMatchObject({ "if-none-match": '"v1"', "if-modified-since": "Mon, 16 Nov 2026 10:00:00 GMT" });
    expect(calls[0]!.headers["if-none-match"]).toBeUndefined();
  });

  it("401, 403 e 451 são bloqueio; outros erros HTTP, corpo grande e demora são erros", async () => {
    const status = (s: number) => () => new Response("x", { status: s });
    const { impl } = net({
      "https://radar-a.pt/401": status(401), "https://radar-a.pt/403": status(403), "https://radar-a.pt/451": status(451),
      "https://radar-a.pt/500": status(500),
      "https://radar-a.pt/grande": () => new Response("a".repeat(5000), { status: 200 }),
      "https://radar-a.pt/declarado": () => new Response("a", { status: 200, headers: { "content-length": "999999999" } }),
      "https://radar-a.pt/lento": () => new Promise<Response>(() => {}),
    });
    const go = (p: string, extra = {}) => safeFetch(`https://radar-a.pt/${p}`, { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns, ...extra });
    for (const s of [401, 403, 451]) expect(await go(String(s))).toMatchObject({ kind: "blocked", status: s });
    expect(await go("500")).toMatchObject({ kind: "error", reason: "http_error", status: 500 });
    expect(await go("grande", { maxBytes: 1000 })).toMatchObject({ kind: "error", reason: "too_large" });
    expect(await go("declarado")).toMatchObject({ kind: "error", reason: "too_large" });
    expect(await go("lento", { timeoutMs: 50 })).toMatchObject({ kind: "error", reason: "timeout" });
  });

  it("descodifica feeds em ISO-8859-1", async () => {
    const latin1 = Buffer.from(rss(item("Habitação em Coimbra", "https://radar-a.pt/l1")).replace("UTF-8", "ISO-8859-1"), "latin1");
    const { impl } = net({ "https://radar-a.pt/latin": () => new Response(latin1, { status: 200, headers: { "content-type": "application/xml" } }) });
    const res = await safeFetch("https://radar-a.pt/latin", { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    expect(res.kind).toBe("ok");
    if (res.kind === "ok") expect(parseFeed(res.body).entries[0]!.title).toBe("Habitação em Coimbra");
  });
});

// ---------------------------------------------------------------- relevância
describe("relevância e temas", () => {
  it("explica as palavras que contaram e dá bónus às fontes primárias e institucionais", () => {
    const s = scoreItem({ title: "Câmara de Coimbra aprova rendas acessíveis para estudantes", excerpt: "O metrobus também." });
    expect(s.topics.slice(0, 1)).toEqual(["local"]);
    expect(s.topics).toEqual(expect.arrayContaining(["habitacao", "universidade", "transportes"]));
    expect(s.matches).toContainEqual({ topic: "local", keyword: "coimbra", field: "title", points: 18 });
    expect(s.matches).toContainEqual({ topic: "transportes", keyword: "metrobus", field: "excerpt", points: 5 });
    expect(s.reasons.join(" ")).toContain("«coimbra» no título");
    const media = scoreItem({ title: "INE: desemprego desce", tier: "media" });
    const prim = scoreItem({ title: "INE: desemprego desce", tier: "primary" });
    const inst = scoreItem({ title: "INE: desemprego desce", tier: "institutional" });
    expect(prim.relevance - media.relevance).toBe(20);
    expect(inst.relevance - media.relevance).toBe(15);
    expect(prim.reasons.at(-1)).toContain("fonte primária");
  });

  it("fica entre 0 e 100, usa prefixos e aceita listas próprias", () => {
    expect(scoreItem({ title: "Nada a ver" }).relevance).toBe(0);
    const tudo = DEFAULT_TOPICS.flatMap((t) => t.keywords.map((k) => k.replace("*", ""))).join(" ");
    expect(scoreItem({ title: tudo, excerpt: tudo, tier: "primary" }).relevance).toBe(100);
    expect(scoreItem({ title: "Novo ano universitário" }).topics).toContain("universidade");
    expect(scoreItem({ title: "Ele ia ao cinema" }).matches.map((m) => m.keyword)).toEqual(["cinema"]); // «ia» não é IA
    const proprio = scoreItem({ title: "Feira do queijo da Serra" }, [{ topic: "gastronomia", label: "Gastronomia", keywords: ["queijo"] }]);
    expect(proprio).toMatchObject({ relevance: 12, topics: ["gastronomia"] });
  });
});

// ---------------------------------------------------------------- radar com a base de dados real
let A: Newsroom, B: Newsroom;
const owner = () => ownerDb();

async function source(n: Newsroom, name: string, feedUrl: string, extra: { tier?: string; interval?: number; active?: boolean } = {}) {
  const [row] = await owner()<{ id: string }[]>`
    insert into feed_sources (publication_id, name, feed_url, tier, interval_minutes, active)
    values (${n.publicationId}, ${name}, ${feedUrl}, ${extra.tier ?? "media"}, ${extra.interval ?? 60}, ${extra.active ?? true})
    returning id`;
  return row!.id;
}
const items = (pub: string) => owner()<{ id: string; url_key: string; title: string; excerpt: string; duplicate_of: string | null;
  feed_source_id: string; relevance: number; topics: string[]; status: string; story_id: string | null }[]>`
  select id, url_key, title, excerpt, duplicate_of, feed_source_id, relevance, topics, status, story_id
  from feed_items where publication_id = ${pub} order by fetched_at, title`;
const sourceRow = async (id: string) => (await owner()<{ last_status: string; last_error: string; etag: string | null;
  last_modified: string | null; last_fetched_at: Date | null }[]>`
  select last_status, last_error, etag, last_modified, last_fetched_at from feed_sources where id = ${id}`)[0]!;

beforeAll(async () => { [A, B] = [await newsroom(), await newsroom()]; });
afterAll(async () => { await closeDb(); await closeOwner(); });

describe("radar: recolha, deduplicação e estado das fontes", () => {
  let s1: string, s2: string, s3: string, s4: string, s5: string, s6: string;
  const feedA = rss(
    item("Câmara de Coimbra aprova novo plano de habitação para estudantes", "https://radar-a.pt/n/plano?utm_source=rss&utm_medium=x",
      `<p>${"Texto longo da notícia. ".repeat(100)}</p>`)
    + item("Metrobus começa a circular na Baixa", "https://radar-a.pt/n/metrobus"));
  const feedB = rss(
    item("Plano de habitação para estudantes: Câmara de Coimbra aprova", "https://radar-b.pt/artigo/123")  // a mesma notícia
    + item("Câmara de Coimbra aprova novo plano de habitação para estudantes", "https://www.radar-a.pt/n/plano/#topo") // o mesmo URL
    + item("Festival de teatro abre portas", "https://radar-b.pt/artigo/124"));
  const routes = {
    "https://radar-a.pt/feed": xml(feedA, { etag: '"a1"', "last-modified": "Mon, 16 Nov 2026 10:00:00 GMT" }),
    "https://radar-b.pt/feed": xml(feedB),
    "https://radar-b.pt/fechado": () => new Response("proibido", { status: 403 }),
    "https://radar-b.pt/lixo": xml("<html><body>isto não é um feed</body></html>"),
    "https://radar-b.pt/rebenta": () => { throw new TypeError("ligação recusada"); },
  };

  beforeAll(async () => {
    s1 = await source(A, "Fonte A", "https://radar-a.pt/feed", { tier: "institutional" });
    s2 = await source(A, "Fonte B", "https://radar-b.pt/feed");
    s3 = await source(A, "Fechada", "https://radar-b.pt/fechado");
    s4 = await source(A, "Lixo", "https://radar-b.pt/lixo");
    s5 = await source(A, "Rebenta", "https://radar-b.pt/rebenta");
    s6 = await source(A, "Fora da lista", "https://nao-permitido.pt/feed");
    await source(A, "Inactiva", "https://radar-a.pt/inactiva", { active: false });
  });

  it("uma fonte com problemas não impede as outras; cada uma fica com o seu estado", async () => {
    const { impl } = net(routes);
    const run = await runRadar(A.publicationId, { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    const by = Object.fromEntries(run.sources.map((s) => [s.name, s]));
    expect(Object.keys(by).sort()).toEqual(["Fechada", "Fonte A", "Fonte B", "Fora da lista", "Lixo", "Rebenta"]); // a inactiva não corre
    expect(by["Fechada"]!.status).toBe("blocked");
    expect(by["Lixo"]).toMatchObject({ status: "error", inserted: 0 });
    expect(by["Rebenta"]).toMatchObject({ status: "error" });
    expect(by["Fora da lista"]).toMatchObject({ status: "error" });
    expect(by["Fonte A"]).toMatchObject({ status: "ok", entries: 2, inserted: 2 });
    expect((await sourceRow(s3)).last_status).toBe("blocked");
    expect((await sourceRow(s4))).toMatchObject({ last_status: "error", last_error: "O documento não é RSS nem Atom." });
    expect((await sourceRow(s5)).last_error).toContain("ligação recusada");
    expect((await sourceRow(s6)).last_error).toContain("não está na lista");
    expect(await sourceRow(s1)).toMatchObject({ last_status: "ok", last_error: "", etag: '"a1"', last_modified: "Mon, 16 Nov 2026 10:00:00 GMT" });
    for (const id of [s1, s2, s3, s4, s5, s6]) expect((await sourceRow(id)).last_fetched_at).toBeInstanceOf(Date);
  });

  it("deduplica: o mesmo URL entra uma vez e a mesma notícia noutra fonte aponta para a primeira", async () => {
    const rows = await items(A.publicationId);
    expect(rows.map((r) => r.url_key).sort()).toEqual([
      "radar-a.pt/n/metrobus", "radar-a.pt/n/plano", "radar-b.pt/artigo/123", "radar-b.pt/artigo/124"]);
    const original = rows.find((r) => r.url_key === "radar-a.pt/n/plano")!;
    const copia = rows.find((r) => r.url_key === "radar-b.pt/artigo/123")!;
    expect(original.feed_source_id).toBe(s1);
    expect(original.duplicate_of).toBeNull();
    expect(copia.duplicate_of).toBe(original.id);
    expect(rows.find((r) => r.url_key === "radar-b.pt/artigo/124")!.duplicate_of).toBeNull();
    const fonteB = (await sourceRow(s2));
    expect(fonteB.last_status).toBe("ok");
    // pontuação guardada, com bónus da fonte institucional, e excerto curto
    expect(original.topics).toEqual(expect.arrayContaining(["local", "habitacao", "universidade"]));
    expect(original.relevance).toBeGreaterThan(copia.relevance);
    for (const r of rows) expect(r.excerpt.length).toBeLessThanOrEqual(300);
  });

  it("voltar a correr não duplica nada; uma fonte acabada de ler só corre se for forçada", async () => {
    const before = (await items(A.publicationId)).length;
    const { impl, calls } = net(routes);
    const idle = await runRadar(A.publicationId, { allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    expect(idle.sources).toEqual([]);
    expect(calls).toHaveLength(0);
    const forced = await runRadar(A.publicationId, { sourceIds: [s2], allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    expect(forced.sources).toHaveLength(1);
    expect(forced.sources[0]).toMatchObject({ status: "ok", entries: 3, inserted: 0, skipped: 3 });
    expect((await items(A.publicationId)).length).toBe(before);
  });

  it("um feed sem alterações (304) não mexe nas entradas e mantém os validadores", async () => {
    const { impl, calls } = net({ "https://radar-a.pt/feed": () => new Response(null, { status: 304 }) });
    const run = await runRadar(A.publicationId, { sourceIds: [s1], allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    expect(run.sources[0]).toMatchObject({ status: "not_modified", inserted: 0 });
    expect(calls[0]!.headers).toMatchObject({ "if-none-match": '"a1"', "if-modified-since": "Mon, 16 Nov 2026 10:00:00 GMT" });
    expect(await sourceRow(s1)).toMatchObject({ last_status: "not_modified", etag: '"a1"' });
  });

  it("um 403 depois de um sucesso marca a fonte como bloqueada", async () => {
    const { impl } = net({ "https://radar-a.pt/feed": () => new Response("", { status: 403 }) });
    const run = await runRadar(A.publicationId, { sourceIds: [s1], allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    expect(run.sources[0]!.status).toBe("blocked");
    expect(await sourceRow(s1)).toMatchObject({ last_status: "blocked", etag: '"a1"' });
    expect((await sourceRow(s1)).last_error).toContain("403");
  });
});

describe("radar: permissões e isolamento", () => {
  let itemA: string, srcA: string;

  beforeAll(async () => {
    srcA = await source(A, "Fonte do teste de permissões", "https://radar-a.pt/perm");
    const { impl } = net({ "https://radar-a.pt/perm": xml(rss(
      item("Universidade de Coimbra abre residência", "https://radar-a.pt/p/1")
      + item("Greve nos transportes públicos", "https://radar-a.pt/p/2")
      + item("Concerto no TAGV", "https://radar-a.pt/p/3"))) });
    await runRadar(A.publicationId, { sourceIds: [srcA], allowlist: ALLOW, fetchImpl: impl, resolve: publicDns });
    itemA = (await items(A.publicationId)).find((r) => r.url_key === "radar-a.pt/p/1")!.id;
  });

  it("só o sistema insere entradas: pessoas e agentes são recusados pela base de dados", async () => {
    const insert = (ctx: Parameters<typeof withCtx>[0], key: string) => withCtx(ctx, (tx) => tx`
      insert into feed_items (publication_id, feed_source_id, url, url_key, title, title_key)
      values (${A.publicationId}, ${srcA}, ${`https://radar-a.pt/${key}`}, ${`radar-a.pt/${key}`}, 'manual', 'manual')`);
    await expect(insert(A.as("admin"), "h1")).rejects.toMatchObject({ code: "42501" });
    await expect(insert(A.as("editor"), "h2")).rejects.toMatchObject({ code: "42501" });
    await expect(insert(agentCtx(A.publicationId, "editorial.radar"), "ag")).rejects.toMatchObject({ code: "42501" });
    await expect(insert(systemCtx(A.publicationId), "sys")).resolves.toBeDefined();
    const excessivo = withCtx(systemCtx(A.publicationId), (tx) => tx`
      insert into feed_items (publication_id, feed_source_id, url, url_key, title, title_key, excerpt)
      values (${A.publicationId}, ${srcA}, 'https://radar-a.pt/x', 'radar-a.pt/x', 'x', 'x', ${"a".repeat(321)})`);
    await expect(excessivo).rejects.toMatchObject({ code: "23514" }); // o limite do excerto também está na base de dados
  });

  it("promover a ideia (sistema): cria uma ideia de origem radar, visível à redacção, e liga a entrada", async () => {
    const { story } = await promoteToIdea(systemCtx(A.publicationId, "radar"), itemA);
    expect(story).toMatchObject({ state: "idea", origin: "radar", created_by: null, title: "Universidade de Coimbra abre residência" });
    expect(story.angle.startsWith("Ver: https://radar-a.pt/p/1")).toBe(true);
    expect(story.angle).toContain("Resumo curto.");
    const row = (await items(A.publicationId)).find((r) => r.id === itemA)!;
    expect(row).toMatchObject({ status: "linked", story_id: story.id });
    await withCtx(A.as("reviewer"), async (tx) => {
      expect((await tx`select id from stories where id = ${story.id}`).length).toBe(1);
      expect((await tx`select status from feed_items where id = ${itemA}`)[0]!.status).toBe("linked");
    });
    await expect(promoteToIdea(A.as("editor"), itemA)).rejects.toThrow("já deu origem");
  });

  it("promover a ideia (pessoa): a ideia fica em nome de quem a promoveu; leitura e agentes não podem", async () => {
    const id = (await items(A.publicationId)).find((r) => r.url_key === "radar-a.pt/p/2")!.id;
    await expect(promoteToIdea(A.as("reviewer"), id)).rejects.toBeInstanceOf(EditorialError);
    await expect(promoteToIdea(agentCtx(A.publicationId, "editorial.radar"), id)).rejects.toBeInstanceOf(EditorialError);
    const { story } = await promoteToIdea(A.as("journalist"), id);
    expect(story).toMatchObject({ state: "idea", origin: "human", created_by: A.users.journalist!.id });
    expect((await items(A.publicationId)).find((r) => r.id === id)).toMatchObject({ status: "linked", story_id: story.id });
  });

  it("pôr de lado uma entrada", async () => {
    const id = (await items(A.publicationId)).find((r) => r.url_key === "radar-a.pt/p/3")!.id;
    await expect(dismissItem(A.as("reviewer"), id)).rejects.toBeInstanceOf(EditorialError);
    await dismissItem(A.as("editor"), id);
    expect((await items(A.publicationId)).find((r) => r.id === id)!.status).toBe("dismissed");
    await expect(dismissItem(A.as("editor"), id)).rejects.toThrow("já foi tratada");
  });

  it("outra publicação nunca vê nem mexe nas entradas e fontes da primeira", async () => {
    const own = (await items(A.publicationId)).length;
    expect(own).toBeGreaterThan(0);
    for (const ctx of [B.as("admin"), systemCtx(B.publicationId), agentCtx(B.publicationId, "editorial.radar")]) {
      await withCtx(ctx, async (tx) => {
        expect((await tx`select 1 from feed_items`).length).toBe(0);
        expect((await tx`select 1 from feed_sources`).length).toBe(0);
        expect((await tx`update feed_items set status = 'dismissed' where id = ${itemA} returning id`).length).toBe(0);
      });
    }
    await expect(promoteToIdea(systemCtx(B.publicationId), itemA)).rejects.toThrow("Não encontrei");
    await expect(dismissItem(B.as("editor"), itemA)).rejects.toBeInstanceOf(EditorialError);
    // o radar de B não corre as fontes de A, mesmo que lhe passem os ids
    const run = await runRadar(B.publicationId, { sourceIds: [srcA], allowlist: ALLOW, fetchImpl: net({}).impl, resolve: publicDns });
    expect(run.sources).toEqual([]);
    expect((await items(B.publicationId)).length).toBe(0);
    expect((await items(A.publicationId)).length).toBe(own);
  });
});

describe("radar: tarefa agendada", () => {
  it("runRadarAll corre cada publicação com o seu próprio contexto", async () => {
    await owner()`update feed_sources set last_fetched_at = null where publication_id = ${A.publicationId}`;
    const runs = await runRadarAll({ allowlist: ALLOW, fetchImpl: net({}).impl, resolve: publicDns });
    const byPub = Object.fromEntries(runs.map((r) => [r.publicationId, r]));
    expect(byPub[A.publicationId]!.sources.length).toBeGreaterThan(0);
    expect(byPub[A.publicationId]!.sources.every((s) => s.status === "error")).toBe(true); // 404 ou fora da lista
    expect(byPub[B.publicationId]!.sources).toEqual([]);
  });
});
