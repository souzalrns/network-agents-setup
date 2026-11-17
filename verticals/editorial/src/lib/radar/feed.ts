import { XMLParser, XMLValidator } from "fast-xml-parser";
import { excerpt } from "../text";

/**
 * Leitura de feeds RSS 2.0, RSS 1.0 (RDF) e Atom. Guarda-se só o essencial de cada entrada: título, endereço,
 * data e um excerto curto. Nunca o artigo inteiro (direitos de autor): o excerto é cortado aqui, à entrada.
 */

export interface FeedEntry {
  title: string;
  url: string;
  publishedAt: Date | null;
  /** Excerto em texto simples, no máximo EXCERPT_MAX caracteres (o nome mantém-se por compatibilidade). */
  summaryHtml: string;
}

export interface ParsedFeed {
  format: "rss" | "rdf" | "atom";
  title: string;
  entries: FeedEntry[];
}

export class FeedError extends Error {}

export const EXCERPT_MAX = 300;
const TITLE_MAX = 300;
/** Um feed com mais entradas do que isto é cortado: o radar só precisa das mais recentes. */
export const MAX_ENTRIES = 100;

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  textNodeName: "#text",
  parseTagValue: false,       // títulos como «2026» ficam texto
  parseAttributeValue: false,
  trimValues: true,
  htmlEntities: true,         // &eacute;, &rsquo;… comuns em feeds portugueses
  processEntities: { enabled: true, maxEntityCount: 20, maxEntitySize: 1000, maxTotalExpansions: 500, maxExpandedLength: 20000 },
  maxNestedTags: 60,
});

type Node = unknown;
const asArray = (v: Node): Node[] => (v === undefined || v === null ? [] : Array.isArray(v) ? v : [v]);
const isObj = (v: Node): v is Record<string, Node> => typeof v === "object" && v !== null && !Array.isArray(v);

/** Texto de um nó, qualquer que seja a forma (texto, CDATA, `#text` com atributos, XHTML aninhado). */
function textOf(v: Node): string {
  if (v === undefined || v === null) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) return v.map(textOf).filter(Boolean).join(" ");
  if (isObj(v)) {
    return Object.entries(v).filter(([k]) => !k.startsWith("@_")).map(([, x]) => textOf(x)).filter(Boolean).join(" ");
  }
  return "";
}

const NAMED: Record<string, string> = {
  hellip: "…", ndash: "–", mdash: "—", lsquo: "‘", rsquo: "’", ldquo: "“", rdquo: "”", laquo: "«", raquo: "»",
  ordm: "º", ordf: "ª", euro: "€", deg: "°", middot: "·", bull: "•", copy: "©", reg: "®", szlig: "ß",
};
const ACCENT: Record<string, string> = { acute: "́", grave: "̀", circ: "̂", tilde: "̃", uml: "̈", cedil: "̧" };

/** Entidades que sobreviveram à leitura do XML (HTML escapado duas vezes). `<`, `>` e `&` ficam para o `excerpt`. */
function decodeLeftovers(s: string): string {
  return s
    .replace(/&([a-z]+);/gi, (m, name: string) => NAMED[name] ?? m)
    .replace(/&([a-z])(acute|grave|circ|tilde|uml|cedil);/gi, (_m, l: string, a: string) => (l + ACCENT[a.toLowerCase()]!).normalize("NFC"))
    .replace(/&#(x[0-9a-f]+|\d+);/gi, (m, code: string) => {
    const n = code[0] === "x" || code[0] === "X" ? parseInt(code.slice(1), 16) : parseInt(code, 10);
    if (!Number.isFinite(n) || n === 38 || n === 60 || n === 62 || n > 0x10ffff || (n >= 0xd800 && n <= 0xdfff)) return m;
    return n < 32 && n !== 9 && n !== 10 && n !== 13 ? " " : String.fromCodePoint(n);
  });
}

function cleanTitle(raw: string): string {
  // o título também pode trazer HTML; reutiliza-se o excerto, com outro limite
  return excerpt(decodeLeftovers(raw), TITLE_MAX);
}

function toDate(raw: string): Date | null {
  const s = raw.trim();
  if (!s) return null;
  const t = Date.parse(s);
  if (Number.isNaN(t)) return null;
  return new Date(t);
}

/** Resolve endereços relativos e recusa esquemas que não sejam http(s) (ex.: `javascript:`). */
function absolute(raw: string, base?: string): string | null {
  const s = raw.trim();
  if (!s) return null;
  try {
    const u = base ? new URL(s, base) : new URL(s);
    return u.protocol === "https:" || u.protocol === "http:" ? u.toString() : null;
  } catch {
    return null;
  }
}

function atomLink(links: Node, base?: string): string | null {
  const all = asArray(links);
  const pick = (rel: (r: string) => boolean) => all.find((l) => isObj(l) && rel(String(l["@_rel"] ?? "alternate")));
  const chosen = pick((r) => r === "alternate") ?? pick((r) => r !== "self" && r !== "enclosure" && r !== "replies") ?? all[0];
  if (isObj(chosen)) return absolute(String(chosen["@_href"] ?? ""), base);
  return typeof chosen === "string" ? absolute(chosen, base) : null;
}

function rssLink(item: Record<string, Node>, base?: string): string | null {
  for (const l of asArray(item.link)) {
    const href = isObj(l) ? String(l["@_href"] ?? textOf(l)) : textOf(l);
    const u = absolute(href, base);
    if (u) return u;
  }
  const guid = item.guid;
  const permalink = isObj(guid) ? String(guid["@_isPermaLink"] ?? "true") !== "false" : true;
  if (guid !== undefined && permalink) return absolute(textOf(guid), base);
  return null;
}

function entry(title: string, url: string | null, date: string, summary: string): FeedEntry | null {
  if (!url) return null;
  const summaryText = excerpt(decodeLeftovers(summary), EXCERPT_MAX);
  const t = cleanTitle(title) || excerpt(summaryText, 120);
  if (!t) return null;
  return { title: t, url, publishedAt: toDate(date), summaryHtml: summaryText };
}

/**
 * Lê o texto de um feed. Lança `FeedError` se o documento não for RSS nem Atom (ex.: uma página HTML ou lixo);
 * entradas sem endereço ou sem título são ignoradas. `baseUrl` resolve ligações relativas.
 */
export function parseFeed(xml: string, baseUrl?: string): ParsedFeed {
  if (typeof xml !== "string" || !xml.trim()) throw new FeedError("O feed veio vazio.");
  // um feed não precisa de declarar entidades; recusá-las corta à partida a expansão maliciosa (billion laughs)
  if (/<!ENTITY/i.test(xml)) throw new FeedError("O feed declara entidades XML: recusado por segurança.");
  const parsed = parseLenient(xml, baseUrl);
  // tolerante com feeds reais um pouco mal formados (ex.: `&` solto), mas um documento inválido sem
  // nenhuma entrada aproveitável (truncado, cortado a meio) é um erro e não «feed vazio»
  if (!parsed.entries.length) {
    const v = XMLValidator.validate(xml);
    if (v !== true) throw new FeedError(`O feed não é XML válido: ${v.err.msg} (linha ${v.err.line})`.slice(0, 300));
  }
  return parsed;
}

function parseLenient(xml: string, baseUrl?: string): ParsedFeed {
  let doc: Record<string, Node>;
  try {
    doc = parser.parse(xml) as Record<string, Node>;
  } catch (e) {
    throw new FeedError(`O feed não é XML válido: ${(e as Error).message}`.slice(0, 300));
  }
  if (!isObj(doc)) throw new FeedError("O documento não é RSS nem Atom.");

  const rss = doc.rss;
  if (isObj(rss)) {
    const channel = asArray(rss.channel).find(isObj) ?? {};
    const base = absolute(textOf(asArray(channel.link).find((l) => typeof l === "string") ?? ""), baseUrl) ?? baseUrl;
    const entries = asArray(channel.item).filter(isObj).slice(0, MAX_ENTRIES).map((it) =>
      entry(textOf(it.title), rssLink(it, base), textOf(it.pubDate ?? it["dc:date"] ?? it.date),
        textOf(it.description ?? it["content:encoded"] ?? it.summary)));
    return { format: "rss", title: cleanTitle(textOf(channel.title)), entries: entries.filter((e): e is FeedEntry => e !== null) };
  }

  const rdf = doc["rdf:RDF"];
  if (isObj(rdf)) {
    const channel = asArray(rdf.channel).find(isObj) ?? {};
    const entries = asArray(rdf.item).filter(isObj).slice(0, MAX_ENTRIES).map((it) =>
      entry(textOf(it.title), absolute(textOf(it.link), baseUrl) ?? absolute(String(it["@_rdf:about"] ?? ""), baseUrl),
        textOf(it["dc:date"]), textOf(it.description ?? it["content:encoded"])));
    return { format: "rdf", title: cleanTitle(textOf(channel.title)), entries: entries.filter((e): e is FeedEntry => e !== null) };
  }

  const feed = doc.feed ?? doc["atom:feed"];
  if (isObj(feed)) {
    const base = (typeof feed["@_xml:base"] === "string" ? absolute(feed["@_xml:base"], baseUrl) : null) ?? baseUrl;
    const entries = asArray(feed.entry).filter(isObj).slice(0, MAX_ENTRIES).map((it) =>
      entry(textOf(it.title), atomLink(it.link, base), textOf(it.published ?? it.updated ?? it.issued ?? it.modified),
        textOf(it.summary ?? it.content)));
    return { format: "atom", title: cleanTitle(textOf(feed.title)), entries: entries.filter((e): e is FeedEntry => e !== null) };
  }

  throw new FeedError("O documento não é RSS nem Atom.");
}
