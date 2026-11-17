/** Análise de texto em português para os agentes (determinística, sem dependências). */

const COMBINING = /[̀-ͯ]/g;
/** Minúsculas e sem acentos, para comparar. */
export const fold = (s: string) => s.normalize("NFD").replace(COMBINING, "").toLowerCase();

/** Texto sem marcação Markdown básica (ligações ficam só com o texto). */
export function plain(md: string): string {
  return md
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/(\*\*|__)(.+?)\1/g, "$2")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^>\s?/gm, "");
}

export function paragraphs(body: string): string[] {
  return body.split(/\n\s*\n/).map((p) => p.replace(/\s+/g, " ").trim()).filter(Boolean);
}

// abreviaturas que não terminam frase
const ABBR = /\b(Sr|Sra|Dr|Dra|Eng|Prof|Profa|Arq|n\.º|nº|art|Av|p|pp|vol|cf|ex|etc|séc|S\.A|Lda|Exmo|Exma)\.$/i;

/** Divide em frases, respeitando abreviaturas, números decimais e citações entre «». */
export function sentences(text: string): string[] {
  const t = text.replace(/\s+/g, " ").trim();
  if (!t) return [];
  const out: string[] = [];
  let start = 0, depth = 0;
  for (let i = 0; i < t.length; i++) {
    const c = t[i]!;
    if (c === "«" || c === "“") depth++;
    else if ((c === "»" || c === "”") && depth > 0) depth--;
    if ((c === "." || c === "!" || c === "?") && depth === 0) {
      const next = t[i + 1];
      const after = t.slice(i + 1, i + 3);
      if (next !== undefined && next !== " ") continue; // 3.5, a.b
      if (c === "." && ABBR.test(t.slice(Math.max(start, i - 6), i + 1))) continue;
      if (next === " " && /^ [a-zà-ú0-9]/.test(after) && c === ".") continue; // a seguir vem minúscula: não é fim
      out.push(t.slice(start, i + 1).trim());
      start = i + 1;
    }
  }
  const rest = t.slice(start).trim();
  if (rest) out.push(rest);
  return out.filter((s) => s.length > 1);
}

export const words = (s: string) => s.split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w));

export function clip(s: string, max = 160): string {
  const t = s.replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  const cut = t.slice(0, max - 1);
  return `${cut.slice(0, Math.max(cut.lastIndexOf(" "), max - 30))}…`;
}

const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
/** Expressão para uma lista de termos como palavras inteiras (sem acentos, minúsculas: usar com `fold`). */
export const termsRe = (terms: string[]) => new RegExp(`(?<![\\p{L}\\p{N}])(${terms.map((t) => esc(fold(t))).join("|")})(?![\\p{L}\\p{N}])`, "gu");

// ---------------------------------------------------------------- atribuição e marcas de incerteza
export const ATTRIBUTION_VERBS = ["disse", "disseram", "afirmou", "afirmaram", "declarou", "declararam", "referiu", "referiram",
  "explicou", "explicaram", "sublinhou", "acrescentou", "garantiu", "garantiram", "admitiu", "defendeu", "defenderam",
  "considerou", "adiantou", "contou", "frisou", "salientou", "lamentou", "questionou", "respondeu", "assegurou", "apontou",
  "alertou", "anunciou", "indicou", "revelou", "reconheceu", "confirmou", "esclareceu", "argumentou", "insistiu", "acusou",
  "criticou", "reiterou", "notou", "observou", "concluiu", "precisou", "destacou", "lembrou", "lamentaram", "acusaram",
  "criticaram", "alertaram", "contaram", "explicaram", "afirma", "afirmam", "diz", "dizem", "refere", "referem", "explica",
  "explicam", "garante", "garantem", "admite", "admitem", "defende", "defendem", "considera", "consideram", "sublinha",
  "sublinham", "acrescenta", "acrescentam", "lembra", "lembram", "lamenta", "lamentam", "acusa", "acusam", "critica",
  "criticam", "alerta", "alertam", "conta", "contam", "assegura", "asseguram", "declara", "declaram"];
export const ATTRIBUTION_PHRASES = ["segundo", "de acordo com", "em declarações", "citado por", "citada por", "nas palavras de",
  "para o", "para a", "na opinião de", "conforme"];
/** Marcas de fonte documental (dados, relatórios, entidades estatísticas). */
export const DOC_SOURCE_MARKERS = ["segundo", "de acordo com", "dados do", "dados da", "dados de", "relatório", "estudo", "fonte",
  "inquérito", "boletim", "estatísticas", "números do", "números da", "divulgados", "divulgadas", "publicados", "publicadas", "ine",
  "pordata", "eurostat", "diário da república", "portal base", "orçamento"];
export const SOURCE_MARKERS = [...ATTRIBUTION_PHRASES, ...ATTRIBUTION_VERBS, ...DOC_SOURCE_MARKERS];

export const UNCONFIRMED_MARKERS = ["alegadamente", "alegado", "alegada", "alegados", "alegadas", "rumores", "rumor",
  "fontes não identificadas", "fonte não identificada", "não confirmado", "não confirmada", "por confirmar", "supostamente",
  "ao que se diz", "diz-se que", "consta que"];
/** «terá/terão/teria + particípio» (terá recebido, terão dito): condicional de rumor, não o futuro. */
export const RUMOUR_CONDITIONAL = /\b(?:terá|terão|teria|teriam)\s+(?:sido\s+)?[\p{L}]+(?:ado|ada|ados|adas|ido|ida|idos|idas|ito|ita|itos|itas|sto|sta|eito|eita|osto|osta|erto|erta)\b/iu;
export const INFERENCE_MARKERS = ["poderá", "poderão", "deverá", "deverão", "pode vir a", "podem vir a", "poderia", "poderiam",
  "deveria", "deveriam", "é provável", "provavelmente", "prevê-se", "admite-se", "é possível que", "eventualmente",
  "tudo indica", "estima-se", "deverá ser", "possivelmente"];

const reUnconf = termsRe(UNCONFIRMED_MARKERS);
const reInfer = termsRe(INFERENCE_MARKERS);
const reAttrVerb = termsRe(ATTRIBUTION_VERBS);
const reAttrPhrase = termsRe(ATTRIBUTION_PHRASES.filter((p) => p !== "para o" && p !== "para a"));
const reSource = termsRe(SOURCE_MARKERS.filter((p) => p !== "para o" && p !== "para a"));

const found = (re: RegExp, s: string) => { re.lastIndex = 0; return [...fold(s).matchAll(re)].map((m) => m[1]!); };
export const unconfirmedSignals = (s: string) => [...found(reUnconf, s), ...(RUMOUR_CONDITIONAL.test(s) ? ["terá + particípio"] : [])];
export const inferenceSignals = (s: string) => found(reInfer, s);
export const attributionSignals = (s: string) => [...found(reAttrPhrase, s), ...found(reAttrVerb, s)];
const reDocSource = termsRe(DOC_SOURCE_MARKERS);
/** A frase diz de onde vem a informação (pessoa, entidade, documento ou ligação). */
export const hasSourceNearby = (s: string) => found(reSource, s).length > 0 || /\]\(https?:|https?:\/\//.test(s);
/** A frase refere uma fonte documental (para valer também para a frase seguinte). */
export const hasDocSource = (s: string) => found(reDocSource, s).length > 0 || /\]\(https?:|https?:\/\//.test(s);

/** Quem fez a declaração, por heurística. Vazio se não for possível dizer. */
export function attributedTo(s: string): string {
  const t = s.replace(/\s+/g, " ").trim();
  // «segundo X», «de acordo com X»
  let m = t.match(/\b(?:segundo|de acordo com|citad[oa] por|nas palavras de|na opinião de)\s+([^,.;:«»"]{2,90})/i);
  if (m && !/^fontes? não identificad/i.test(m[1]!)) return tidy(m[1]!);
  // «…», disse o presidente da câmara
  const verbs = ATTRIBUTION_VERBS.join("|");
  m = t.match(new RegExp(`[»"”]\\s*,?\\s*(?:${verbs})\\s+([^,.;:«»"]{2,90})`, "iu"));
  if (m) return tidy(m[1]!);
  // O ministro das Finanças disse que…  /  A autarca, Maria Silva, afirmou…
  m = t.match(new RegExp(`^(?:.*?[,;:]\\s+)?([^,;:«»"]{2,120}?)\\s*,?\\s+(?:${verbs})\\b`, "iu"));
  if (m) return tidy(m[1]!);
  return "";
}
const tidy = (s: string) => clip(s.replace(/\s+(que|a|à|ao)$/i, "").trim(), 120);

// ---------------------------------------------------------------- números, datas, instituições, citações
const MONTHS = "janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro";
export const DATE_RE = new RegExp(`\\b(\\d{1,2}\\s+de\\s+(?:${MONTHS})(?:\\s+de\\s+\\d{4})?|(?:em|desde|até|de)\\s+(?:${MONTHS})(?:\\s+de\\s+\\d{4})?|\\d{1,2}/\\d{1,2}/\\d{2,4}|(?:19|20)\\d{2})\\b`, "giu");
export const PERCENT_RE = /\b\d+(?:[.,]\d+)?\s?(?:%|por cento|pontos percentuais|p\.p\.)/giu;
export const MONEY_RE = /(?:€\s?\d[\d.,]*(?:\s?(?:mil|milhões|milhão|mil milhões))?|\b\d[\d.,]*\s?(?:mil milhões|milhões|milhão|mil)?\s?(?:de\s+)?(?:euros|€|dólares|US\$))/giu;
export const NUMBER_RE = /\b\d[\d.,]*\b/g;

export interface Quantity { raw: string; value: number; unit: "percent" | "money" | "count"; metric: string }

const MULT: Record<string, number> = { mil: 1e3, "milhão": 1e6, "milhões": 1e6, "mil milhões": 1e9 };
const parsePt = (n: string) => Number(n.replace(/\.(?=\d{3}\b)/g, "").replace(",", "."));
const STOP_METRIC = new Set(["de", "do", "da", "dos", "das", "em", "e", "a", "o", "os", "as", "no", "na", "por", "para", "que", "mil", "milhões", "milhão", "euros"]);

/** Quantidades com unidade e a palavra que as qualifica («500 pessoas» → métrica «pessoas»). */
export function quantities(s: string): Quantity[] {
  const out: Quantity[] = [];
  const re = /(€\s?)?(\d[\d.,]*)(?:\s?(mil milhões|milhões|milhão|mil)(?![\p{L}]))?(?:\s?(%|por cento|pontos percentuais|(?:de\s+)?euros|€))?((?:\s+[\p{L}-]+){0,3})/giu;
  for (const m of s.matchAll(re)) {
    const [, eur1, rawNum, mult, unitWord, tail] = m;
    const num = rawNum!.replace(/[.,]+$/, "");
    if (/^(19|20)\d{2}$/.test(num) && !mult && !unitWord && !eur1) continue; // um ano não é uma quantidade
    const raw = m[0].slice(0, m[0].length - (tail ?? "").length).replace(/[.,]+$/, "");
    const base = parsePt(num);
    if (!Number.isFinite(base)) continue;
    const value = base * (mult ? MULT[mult.toLowerCase()] ?? 1 : 1);
    const unit = unitWord && /%|cento|percentua/i.test(unitWord) ? "percent" : eur1 || (unitWord && /euro|€/i.test(unitWord)) ? "money" : "count";
    const metric = (tail ?? "").trim().split(/\s+/).map(fold).find((w) => w.length > 2 && !STOP_METRIC.has(w)) ?? "";
    out.push({ raw: raw!.trim(), value, unit, metric });
  }
  return out;
}

const INSTITUTION_HEADS = ["Câmara Municipal", "Câmara", "Ministério", "Ministro", "Ministra", "Instituto", "Tribunal",
  "Universidade", "Hospital", "Agrupamento", "Comissão", "Autoridade", "Direção-Geral", "Direcção-Geral", "Agência", "Banco",
  "Associação", "Sindicato", "Federação", "Junta de Freguesia", "Junta", "Assembleia", "Conselho", "Governo", "Parlamento",
  "Polícia Judiciária", "Ministério Público", "Presidente da República", "Segurança Social", "Autoridade Tributária",
  "Provedor", "Inspeção-Geral", "Inspecção-Geral", "Entidade", "Fundação", "Empresa", "Serviço Nacional de Saúde", "Escola"];
const INSTITUTION_RE = new RegExp(`\\b(?:${INSTITUTION_HEADS.map(esc).join("|")})(?:\\s+(?:de|da|do|dos|das|e)?\\s*[A-ZÀ-Ú][\\p{L}-]+){0,4}`, "gu");
const ACRONYM_RE = /\b[A-ZÀ-Ú]{2,7}\b/g;
const NOT_ACRONYMS = new Set(["UE", "EU", "PS", "TV", "OK", "EUA"]);

/** Instituições e siglas nomeadas na frase. */
export function institutions(s: string): string[] {
  const names = [...s.matchAll(INSTITUTION_RE)].map((m) => m[0].trim());
  const acr = [...s.matchAll(ACRONYM_RE)].map((m) => m[0]).filter((a) => !NOT_ACRONYMS.has(a) && !/^[IVXLC]+$/.test(a));
  return [...new Set([...names, ...acr])];
}

export interface Quote { text: string; index: number }
/** Citações entre «», “” ou "". */
export function quotes(s: string): Quote[] {
  const out: Quote[] = [];
  for (const m of s.matchAll(/«([^»]{1,1200})»|“([^”]{1,1200})”|"([^"\n]{1,1200})"/g)) {
    out.push({ text: (m[1] ?? m[2] ?? m[3] ?? "").trim(), index: m.index ?? 0 });
  }
  return out;
}

export const hasDate = (s: string) => new RegExp(DATE_RE.source, "iu").test(s);
export const isCheckable = (s: string) =>
  /\d/.test(s) || institutions(s).length > 0 || quotes(s).length > 0 || hasDate(s) || unconfirmedSignals(s).length > 0;

/** A frase sem o texto citado (as palavras de quem é citado não são do jornalista). */
export const withoutQuotes = (s: string) => s.replace(/«[^»]*»|“[^”]*”|"[^"\n]*"/g, "«…»");
