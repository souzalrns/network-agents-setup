/**
 * Relevância (0 a 100) e temas de uma entrada do radar, por listas de palavras-chave configuráveis.
 * Explicável: devolve as palavras que contaram, onde apareceram e quantos pontos deram.
 * Uma palavra terminada em `*` é um prefixo (`universit*` apanha «universidade» e «universitário»).
 */

export type Tier = "primary" | "institutional" | "media";

export interface TopicRule {
  /** Identificador do tema, guardado em `feed_items.topics`. */
  topic: string;
  label: string;
  keywords: string[];
  /** Multiplicador dos pontos deste tema (por omissão 1). */
  weight?: number;
}

export interface ScoreInput {
  title: string;
  excerpt?: string;
  tier?: Tier;
}

export interface KeywordMatch {
  topic: string;
  keyword: string;
  field: "title" | "excerpt";
  points: number;
}

export interface ScoreResult {
  relevance: number;
  topics: string[];
  matches: KeywordMatch[];
  tierBonus: number;
  /** Explicação legível, uma linha por razão. */
  reasons: string[];
}

export const POINTS = { title: 12, excerpt: 5, keywordCap: 80 } as const;
export const TIER_BONUS: Record<Tier, number> = { primary: 20, institutional: 15, media: 0 };

const COMBINING = /[̀-ͯ]/g;
/** Minúsculas, sem acentos, só letras e números separados por um espaço, com espaço nas pontas. */
function norm(s: string): string {
  return ` ${s.normalize("NFD").replace(COMBINING, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim()} `;
}

function matcher(keyword: string): ((text: string) => boolean) | null {
  const prefix = keyword.trim().endsWith("*");
  const k = norm(keyword.replace(/\*+$/, "")).trim();
  if (!k) return null;
  return prefix ? (t) => t.includes(` ${k}`) : (t) => t.includes(` ${k} `);
}

export function scoreItem(input: ScoreInput, rules: readonly TopicRule[] = DEFAULT_TOPICS): ScoreResult {
  const title = norm(input.title ?? "");
  const body = norm(input.excerpt ?? "");
  const matches: KeywordMatch[] = [];
  const byTopic = new Map<string, number>();
  for (const rule of rules) {
    const weight = rule.weight ?? 1;
    const seen = new Set<string>();
    for (const kw of rule.keywords) {
      const m = matcher(kw);
      const key = norm(kw).trim();
      if (!m || seen.has(key)) continue;
      const field = m(title) ? "title" : m(body) ? "excerpt" : null;
      if (!field) continue;
      seen.add(key);
      const points = Math.round(POINTS[field] * weight);
      matches.push({ topic: rule.topic, keyword: kw, field, points });
      byTopic.set(rule.topic, (byTopic.get(rule.topic) ?? 0) + points);
    }
  }
  const keywordPoints = Math.min(POINTS.keywordCap, matches.reduce((n, m) => n + m.points, 0));
  const tierBonus = TIER_BONUS[input.tier ?? "media"] ?? 0;
  const relevance = Math.max(0, Math.min(100, keywordPoints + tierBonus));
  const topics = [...byTopic.entries()].sort((a, b) => b[1] - a[1]).map(([t]) => t);
  const reasons = matches.map((m) => `«${m.keyword}» ${m.field === "title" ? "no título" : "no excerto"} (${m.topic}, +${m.points})`);
  if (tierBonus) reasons.push(`fonte ${input.tier === "primary" ? "primária" : "institucional"} (+${tierBonus})`);
  return { relevance, topics, matches, tierBonus, reasons };
}

/** Lista por omissão, em português, centrada em Coimbra. Ajustável por publicação (passa-se outra lista). */
export const DEFAULT_TOPICS: readonly TopicRule[] = [
  { topic: "local", label: "Coimbra e região", weight: 1.5, keywords: [
    "coimbra", "conimbric*", "mondego", "baixa de coimbra", "alta de coimbra", "santa clara", "solum", "celas", "eiras",
    "santo antonio dos olivais", "taveiro", "brasfemes", "torres do mondego", "figueira da foz", "cantanhede", "condeixa",
    "mealhada", "penacova", "lousa", "miranda do corvo", "montemor o velho", "soure", "vila nova de poiares",
    "regiao de coimbra", "cim regiao de coimbra", "camara municipal de coimbra", "assembleia municipal de coimbra",
    "junta de freguesia", "uniao de freguesias"] },
  { topic: "universidade", label: "Universidade e ensino superior", keywords: [
    "universidade de coimbra", "universit*", "uc", "politecnico de coimbra", "ensino superior", "estudantes", "estudante",
    "propinas", "reitor", "reitoria", "associacao academica", "aac", "queima das fitas", "praxe", "bolsas de estudo",
    "residencias universitarias", "academia", "chuc", "hospitais da universidade"] },
  { topic: "habitacao", label: "Habitação", keywords: [
    "habitacao", "habitacional", "rendas", "renda", "arrendamento", "arrendatarios", "senhorios", "alojamento local",
    "alojamento estudantil", "imobiliario", "preco das casas", "precos das casas", "credito a habitacao", "despejo*",
    "porta 65", "1 direito", "ihru", "habitacao publica", "habitacao acessivel"] },
  { topic: "transportes", label: "Transportes e mobilidade", keywords: [
    "metrobus", "metro mondego", "sistema de mobilidade do mondego", "smtuc", "comboio*", "ferrovia", "ferroviari*",
    "linha do norte", "alta velocidade", "autocarro*", "estacao de coimbra b", "mobilidade", "transito", "portagens",
    "ic2", "ip3", "a1", "aeroporto", "ciclovia*", "transportes publicos", "cp"] },
  { topic: "politica", label: "Política", keywords: [
    "governo", "parlamento", "assembleia da republica", "ministro", "ministra", "primeiro ministro", "presidente da republica",
    "conselho de ministros", "autarquicas", "eleicoes", "eleitoral", "vereador*", "vereacao", "presidente da camara",
    "orcamento do estado", "deputado*", "partido*", "decreto lei", "proposta de lei", "projeto de lei", "ps", "psd", "pcp",
    "cds", "bloco de esquerda", "iniciativa liberal", "partido chega", "autarquia*"] },
  { topic: "economia", label: "Economia e trabalho", keywords: [
    "economia", "economic*", "inflacao", "desemprego", "emprego", "salario*", "salario minimo", "pib", "ine",
    "exportacoes", "investimento", "impostos", "irs", "irc", "iva", "banco de portugal", "juros", "euribor",
    "turismo", "prr", "fundos europeus", "greve*", "sindicat*", "empresas", "eurostat"] },
  { topic: "cultura", label: "Cultura", keywords: [
    "cultura", "cultural", "teatro", "musica", "concerto*", "festival", "exposicao", "museu", "cinema", "livro*",
    "literatura", "patrimonio", "unesco", "tagv", "gil vicente", "convento sao francisco", "biblioteca", "fado"] },
  { topic: "ciencia", label: "Ciência e saúde", keywords: [
    "ciencia", "cientific*", "cientistas", "investigacao", "investigador*", "fct", "laboratorio", "descoberta",
    "saude", "cancro", "vacina*", "hospital", "alteracoes climaticas", "clima", "ambiente"] },
  { topic: "tecnologia", label: "Tecnologia", keywords: [
    "tecnologia*", "tecnologic*", "inteligencia artificial", "digital", "startup*", "software", "ciberseguranca",
    "internet", "5g", "inovacao", "instituto pedro nunes", "dados pessoais", "algoritmo*"] },
  { topic: "desporto", label: "Desporto", keywords: [
    "desporto", "desportiv*", "futebol", "academica", "briosa", "uniao de coimbra", "liga", "taca", "campeonato",
    "atletismo", "natacao", "basquetebol", "andebol", "voleibol", "ciclismo", "maratona", "estadio cidade de coimbra",
    "selecao nacional"] },
];
