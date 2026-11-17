/** Utilitários de texto sem dependências: endereços amigáveis, chaves de deduplicação, excertos. */

const COMBINING = /[̀-ͯ]/g;

export function slugify(input: string, max = 80): string {
  const s = input.normalize("NFD").replace(COMBINING, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return s.slice(0, max).replace(/-+$/g, "") || "sem-titulo";
}

const STOP = new Set(["a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
  "um", "uma", "para", "por", "com", "que", "se", "ao", "aos", "the", "of", "in", "and", "to", "for", "on"]);

/** Chave de título para reconhecer a mesma notícia em meios diferentes (ordem das palavras não conta). */
export function titleKey(title: string): string {
  const words = title.normalize("NFD").replace(COMBINING, "").toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter((w) => w.length > 2 && !STOP.has(w));
  return [...new Set(words)].sort().join(" ");
}

const TRACKING = /^(utm_|fbclid$|gclid$|mc_cid$|mc_eid$|ref$|ref_src$|igshid$|cmpid$|ocid$)/i;

/** URL normalizado: sem fragmento, sem parâmetros de seguimento, host em minúsculas, sem barra final. */
export function urlKey(raw: string): string | null {
  let u: URL;
  try { u = new URL(raw); } catch { return null; }
  if (u.protocol !== "https:" && u.protocol !== "http:") return null;
  u.hash = "";
  for (const k of [...u.searchParams.keys()]) if (TRACKING.test(k)) u.searchParams.delete(k);
  u.searchParams.sort();
  const host = u.hostname.toLowerCase().replace(/^www\./, "");
  const path = u.pathname.replace(/\/+$/, "") || "/";
  const q = u.searchParams.toString();
  return `${host}${path}${q ? `?${q}` : ""}`;
}

/** Texto simples a partir de HTML de um feed, cortado: guarda-se um excerto curto, nunca o artigo. */
export function excerpt(html: string, max = 300): string {
  const text = html.replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ").replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/\s+/g, " ").trim();
  if (text.length <= max) return text;
  const cut = text.slice(0, max - 1);
  return `${cut.slice(0, Math.max(cut.lastIndexOf(" "), max - 40))}…`;
}

/** Semelhança de Jaccard entre duas chaves de título (0 a 1). */
export function similarity(a: string, b: string): number {
  const A = new Set(a.split(" ").filter(Boolean)), B = new Set(b.split(" ").filter(Boolean));
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const w of A) if (B.has(w)) inter++;
  return inter / (A.size + B.size - inter);
}
