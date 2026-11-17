/**
 * Contratos dos agentes da redacção: tipos e validação em tempo de execução.
 *
 * Um agente nunca decide: produz uma PROPOSTA tipada que uma pessoa aceita ou rejeita. Tudo o que um agente
 * grava passa por aqui; uma saída inválida (incluindo a de um modelo de linguagem) é recusada, nunca guardada.
 */

// ---------------------------------------------------------------- identidades
export const AGENT_IDS = ["editorial.radar", "editorial.research", "editorial.factcheck", "editorial.editor"] as const;
export type AgentId = (typeof AGENT_IDS)[number];
export const isAgentId = (v: unknown): v is AgentId => typeof v === "string" && (AGENT_IDS as readonly string[]).includes(v);

export type OutputKind = "story_suggestions" | "research_dossier" | "factcheck_report" | "edit_review";
export const OUTPUT_KIND: Record<AgentId, OutputKind> = {
  "editorial.radar": "story_suggestions",
  "editorial.research": "research_dossier",
  "editorial.factcheck": "factcheck_report",
  "editorial.editor": "edit_review",
};

// ---------------------------------------------------------------- blocos comuns
/** Os quatro tipos de afirmação do contrato de dados (tabela `claims`). */
export const CLAIM_KINDS = ["fact", "statement", "inference", "unconfirmed"] as const;
export type ClaimKind = (typeof CLAIM_KINDS)[number];

/** Evidência: sempre um endereço do material fornecido. `candidate` = por confirmar por uma pessoa. */
export interface Evidence { url: string; title: string; quote: string; relation: "candidate" | "cited" }

/** Uma afirmação numa saída de agente: diz sempre o tipo e a evidência (que pode estar vazia). */
export interface ClaimRecord { text: string; kind: ClaimKind; attributed_to: string; evidence: Evidence[] }

export interface Cost { calls: number; input_tokens: number; output_tokens: number; usd_estimate: number }
export const zeroCost = (): Cost => ({ calls: 0, input_tokens: 0, output_tokens: 0, usd_estimate: 0 });

/** O que aconteceu ao passo opcional com modelo de linguagem. */
export interface LlmInfo {
  status: "not_configured" | "skipped" | "used" | "rejected" | "stopped" | "error";
  model: string;
  reason: string;
}

export interface OutputBase {
  schema_version: 1;
  agent_id: AgentId;
  run_id: string;
  kind: OutputKind;
  generated_at: string;
  /** Proposta para uma pessoa aceitar ou rejeitar; nunca uma decisão. */
  proposal: true;
  inputs: Record<string, unknown>;
  /** Endereços do material efectivamente usado (nunca inventados). */
  sources_used: string[];
  cost: Cost;
  llm: LlmInfo;
  notes: string[];
}

// ---------------------------------------------------------------- revisão de edição
export type Severity = "info" | "warning" | "blocker";
export const SEVERITIES: Severity[] = ["info", "warning", "blocker"];
export type ArticleField = "title" | "subtitle" | "summary" | "body" | "seo_title" | "meta_description" | "claims";

export interface Finding { severity: Severity; rule: string; field: ArticleField; excerpt: string; suggestion: string }

/** Sugestão de texto (do modelo): só proposta, nunca aplicada à peça. */
export interface TextSuggestion { rule: string; excerpt: string; suggestion: string; origin: "llm" }

export interface ChannelAdaptations {
  draft: true;
  label: string;
  instagram_carousel: { slides: { n: number; text: string }[] };
  reel_script: { target_seconds: { min: 45; max: 60 }; beats: { from_s: number; to_s: number; text: string }[] };
  youtube_description: { text: string };
  podcast_points: { points: string[] };
}

export interface EditReview extends OutputBase {
  kind: "edit_review";
  story: { id: string; version: number; state: string };
  findings: Finding[];
  counts: Record<Severity, number>;
  adaptations: ChannelAdaptations;
  suggestions: TextSuggestion[];
}

// ---------------------------------------------------------------- verificação
export interface CheckedClaim extends ClaimRecord {
  claim_id: string | null;
  /** true se a linha foi criada nesta execução; false se já existia (não se duplica). */
  created: boolean;
  verification: "pending" | "verified" | "disputed" | "unsupported";
  signals: string[];
  /** A mesma informação noutros meios. Repetição NÃO é verificação. */
  repetition: { url: string; title: string }[];
}

export interface Contradiction { entity: string; unit: string; metric: string; values: string[]; sentences: string[] }

export interface LlmClaimOpinion { text: string; kind: ClaimKind; attributed_to: string; note: string }

export interface FactcheckReport extends OutputBase {
  kind: "factcheck_report";
  story: { id: string; version: number; state: string };
  claims: CheckedClaim[];
  counts: Record<ClaimKind, number>;
  contradictions: Contradiction[];
  rules: string[];
  second_opinion: LlmClaimOpinion[];
}

// ---------------------------------------------------------------- dossier de investigação
export interface BackgroundItem {
  title: string; url: string; source: string; published_at: string | null;
  origin: "story_ref" | "feed_item"; relation: string; excerpt: string;
}
export interface PrimarySource { label: string; url: string; why: string; status: "por consultar" }

export interface ResearchDossier extends OutputBase {
  kind: "research_dossier";
  story: { id: string; version: number; state: string };
  pitch: { title: string; angle: string; to_confirm: string };
  background: BackgroundItem[];
  timeline: { date: string; title: string; url: string }[];
  primary_sources: PrimarySource[];
  open_questions: string[];
  interview_questions: string[];
  summary: { text: string; points: ClaimRecord[] } | null;
}

// ---------------------------------------------------------------- sugestões do radar
export interface Cluster {
  title: string;
  why: string;
  item_ids: string[];
  item_urls: string[];
  sources: string[];
  sources_count: number;
  topics: string[];
  latest_at: string | null;
  score: number;
  /** Nome da editoria sugerida (texto, para mostrar) e o seu id. */
  suggested_section: string | null;
  suggested_section_id: string | null;
  idea_story_id: string | null;
  proposed_title: string | null;
  proposed_angle: string | null;
}

export interface StorySuggestions extends OutputBase {
  kind: "story_suggestions";
  window_hours: number;
  items_considered: number;
  clusters: Cluster[];
}

export type AgentOutput = EditReview | FactcheckReport | ResearchDossier | StorySuggestions;

// ================================================================ validação em tempo de execução
export type Validation<T> = { ok: true; value: T } | { ok: false; errors: string[] };

type Check = (v: unknown, path: string, errs: string[]) => void;

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (max = 20_000): Check => (v, p, e) => {
  if (typeof v !== "string") e.push(`${p}: deve ser texto`);
  else if (v.length > max) e.push(`${p}: texto demasiado longo (${v.length} > ${max})`);
};
const nonEmpty = (max = 20_000): Check => (v, p, e) => {
  str(max)(v, p, e);
  if (typeof v === "string" && !v.trim()) e.push(`${p}: não pode estar vazio`);
};
const num: Check = (v, p, e) => { if (typeof v !== "number" || !Number.isFinite(v) || v < 0) e.push(`${p}: deve ser um número >= 0`); };
const bool: Check = (v, p, e) => { if (typeof v !== "boolean") e.push(`${p}: deve ser verdadeiro/falso`); };
const oneOf = (vals: readonly string[]): Check => (v, p, e) => {
  if (typeof v !== "string" || !vals.includes(v)) e.push(`${p}: valor inválido (${String(v)}); esperado ${vals.join("|")}`);
};
const literal = (val: unknown): Check => (v, p, e) => { if (v !== val) e.push(`${p}: deve ser ${JSON.stringify(val)}`); };
const nullable = (c: Check): Check => (v, p, e) => { if (v !== null) c(v, p, e); };
const httpUrl: Check = (v, p, e) => {
  if (typeof v !== "string" || !/^https?:\/\/[^\s]+$/i.test(v)) e.push(`${p}: endereço inválido`);
};
const arr = (item: Check, max = 500): Check => (v, p, e) => {
  if (!Array.isArray(v)) { e.push(`${p}: deve ser uma lista`); return; }
  if (v.length > max) e.push(`${p}: lista demasiado longa (${v.length} > ${max})`);
  v.forEach((x, i) => item(x, `${p}[${i}]`, e));
};
const obj = (shape: Record<string, Check>): Check => (v, p, e) => {
  if (!isObj(v)) { e.push(`${p}: deve ser um objecto`); return; }
  for (const [k, c] of Object.entries(shape)) c(v[k], `${p}.${k}`, e);
};
const anyRecord: Check = (v, p, e) => { if (!isObj(v)) e.push(`${p}: deve ser um objecto`); };

const evidenceCheck = obj({ url: httpUrl, title: str(500), quote: str(2000), relation: oneOf(["candidate", "cited"]) });
/** Uma declaração tem sempre autor (o mesmo que a base de dados exige). */
const claimCheck = (extra: Record<string, Check> = {}): Check => (v, p, e) => {
  obj({ text: nonEmpty(2000), kind: oneOf(CLAIM_KINDS), attributed_to: str(300), evidence: arr(evidenceCheck, 50), ...extra })(v, p, e);
  if (isObj(v) && v.kind === "statement" && (typeof v.attributed_to !== "string" || !v.attributed_to.trim())) {
    e.push(`${p}.attributed_to: uma declaração (statement) diz sempre quem a fez`);
  }
};
const costCheck = obj({ calls: num, input_tokens: num, output_tokens: num, usd_estimate: num });
const storyRef = obj({ id: nonEmpty(64), version: num, state: nonEmpty(40) });

const base = (kind: OutputKind): Record<string, Check> => ({
  schema_version: literal(1),
  agent_id: oneOf(AGENT_IDS),
  run_id: nonEmpty(100),
  kind: literal(kind),
  generated_at: nonEmpty(40),
  proposal: literal(true),
  inputs: anyRecord,
  sources_used: arr(httpUrl, 500),
  cost: costCheck,
  llm: obj({ status: oneOf(["not_configured", "skipped", "used", "rejected", "stopped", "error"]), model: str(100), reason: str(1000) }),
  notes: arr(str(1000), 50),
});

const SHAPES: Record<OutputKind, Record<string, Check>> = {
  edit_review: {
    ...base("edit_review"),
    story: storyRef,
    findings: arr(obj({
      severity: oneOf(SEVERITIES), rule: nonEmpty(80),
      field: oneOf(["title", "subtitle", "summary", "body", "seo_title", "meta_description", "claims"]),
      excerpt: str(400), suggestion: nonEmpty(1000),
    })),
    counts: obj({ info: num, warning: num, blocker: num }),
    adaptations: obj({
      draft: literal(true), label: nonEmpty(300),
      instagram_carousel: obj({ slides: arr(obj({ n: num, text: nonEmpty(400) }), 10) }),
      reel_script: obj({ target_seconds: obj({ min: literal(45), max: literal(60) }),
        beats: arr(obj({ from_s: num, to_s: num, text: nonEmpty(600) }), 10) }),
      youtube_description: obj({ text: str(5000) }),
      podcast_points: obj({ points: arr(nonEmpty(600), 12) }),
    }),
    suggestions: arr(obj({ rule: nonEmpty(80), excerpt: nonEmpty(400), suggestion: nonEmpty(1000), origin: literal("llm") }), 30),
  },
  factcheck_report: {
    ...base("factcheck_report"),
    story: storyRef,
    claims: arr(claimCheck({
      claim_id: nullable(nonEmpty(64)), created: bool,
      verification: oneOf(["pending", "verified", "disputed", "unsupported"]),
      signals: arr(str(200), 20), repetition: arr(obj({ url: httpUrl, title: str(500) }), 50),
    })),
    counts: obj({ fact: num, statement: num, inference: num, unconfirmed: num }),
    contradictions: arr(obj({ entity: nonEmpty(200), unit: nonEmpty(40), metric: str(80),
      values: arr(nonEmpty(80), 20), sentences: arr(nonEmpty(2000), 20) })),
    rules: arr(nonEmpty(400), 20),
    second_opinion: arr(obj({ text: nonEmpty(2000), kind: oneOf(CLAIM_KINDS), attributed_to: str(300), note: str(600) }), 50),
  },
  research_dossier: {
    ...base("research_dossier"),
    story: storyRef,
    pitch: obj({ title: nonEmpty(500), angle: str(5000), to_confirm: str(5000) }),
    background: arr(obj({ title: str(500), url: httpUrl, source: str(200), published_at: nullable(nonEmpty(40)),
      origin: oneOf(["story_ref", "feed_item"]), relation: nonEmpty(80), excerpt: str(400) }), 100),
    timeline: arr(obj({ date: nonEmpty(40), title: str(500), url: httpUrl }), 100),
    primary_sources: arr(obj({ label: nonEmpty(200), url: httpUrl, why: nonEmpty(400), status: literal("por consultar") }), 20),
    open_questions: arr(nonEmpty(600), 30),
    interview_questions: arr(nonEmpty(600), 30),
    summary: nullable(obj({ text: nonEmpty(4000), points: arr(claimCheck(), 30) })),
  },
  story_suggestions: {
    ...base("story_suggestions"),
    window_hours: num,
    items_considered: num,
    clusters: arr(obj({
      title: nonEmpty(500), why: nonEmpty(1000), item_ids: arr(nonEmpty(64), 200), item_urls: arr(httpUrl, 200),
      sources: arr(str(200), 100), sources_count: num, topics: arr(str(80), 30), latest_at: nullable(nonEmpty(40)),
      score: num, suggested_section: nullable(nonEmpty(200)), suggested_section_id: nullable(nonEmpty(64)),
      idea_story_id: nullable(nonEmpty(64)), proposed_title: nullable(nonEmpty(200)), proposed_angle: nullable(nonEmpty(600)),
    }), 50),
  },
};

/** Valida uma saída completa de agente antes de a guardar. */
export function validateOutput(v: unknown): Validation<AgentOutput> {
  const errs: string[] = [];
  if (!isObj(v) || typeof v.kind !== "string" || !(v.kind in SHAPES)) return { ok: false, errors: ["saída: tipo desconhecido"] };
  obj(SHAPES[v.kind as OutputKind])(v, "saída", errs);
  if (isObj(v) && isAgentId(v.agent_id) && OUTPUT_KIND[v.agent_id] !== v.kind) errs.push("saída: tipo não corresponde ao agente");
  return errs.length ? { ok: false, errors: errs } : { ok: true, value: v as unknown as AgentOutput };
}

// ---------------------------------------------------------------- respostas do modelo (antes de as juntar)
/** Validadores das respostas JSON do modelo; cada agente acrescenta as verificações de conteúdo. */
export const llmShapes = {
  editSuggestions: obj({ suggestions: arr(obj({ rule: nonEmpty(80), excerpt: nonEmpty(400), suggestion: nonEmpty(1000) }), 30) }),
  claimOpinions: obj({ claims: arr(obj({ text: nonEmpty(2000), kind: oneOf(CLAIM_KINDS), attributed_to: str(300), note: str(600) }), 50) }),
  summary: obj({ summary: nonEmpty(4000), points: arr(obj({ text: nonEmpty(2000), kind: oneOf(CLAIM_KINDS),
    attributed_to: str(300), items: arr(num, 20) }), 30) }),
  clusterTitles: obj({ clusters: arr(obj({ n: num, title: nonEmpty(200), angle: nonEmpty(600) }), 50) }),
};

export function check<T>(shape: Check, v: unknown, label = "resposta"): Validation<T> {
  const errs: string[] = [];
  shape(v, label, errs);
  return errs.length ? { ok: false, errors: errs } : { ok: true, value: v as T };
}
