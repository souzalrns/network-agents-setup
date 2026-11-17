/**
 * Verificação (`editorial.factcheck`). Extrai do texto as frases verificáveis (números, valores, datas,
 * instituições, citações), classifica cada uma num dos quatro tipos e regista-as como afirmações PENDENTES.
 * Nunca marca nada como verificado (a base de dados também o impede) e a repetição noutros meios nunca
 * conta como verificação.
 */
import type { Ctx } from "../context";
import { withCtx } from "../db";
import { similarity, titleKey } from "../text";
import {
  type CheckedClaim, check, type ClaimKind, type Contradiction, type Evidence, type FactcheckReport, type LlmClaimOpinion, llmShapes,
} from "./contracts";
import { llmJson, material } from "./llm";
import { type AgentOpts, type AgentResult, agentEnv, envelope, loadClaims, loadRefs, type RefRow, storyFor } from "./shared";
import {
  attributedTo, attributionSignals, clip, DATE_RE, fold, inferenceSignals, institutions, isCheckable, MONEY_RE, PERCENT_RE,
  paragraphs, plain, quantities, quotes, sentences, unconfirmedSignals,
} from "./textkit";

export const AGENT_ID = "editorial.factcheck" as const;

export const RULES = [
  "As afirmações criadas pelo agente ficam sempre pendentes: só uma pessoa as verifica, com evidência.",
  "A repetição da mesma informação noutros meios nunca torna uma afirmação verificada.",
  "Uma declaração diz sempre quem a fez; uma inferência apresenta-se como hipótese.",
  "Informação não confirmada não pode ir no artigo.",
  "As afirmações propostas entram com in_article = falso: é a redacção que confirma que estão no artigo.",
];

export interface Classified { kind: ClaimKind; attributed_to: string; signals: string[] }

/**
 * Classifica uma frase. Ordem: não confirmada > declaração > inferência > facto
 * (na dúvida, o tipo mais prudente).
 */
export function classify(sentence: string): Classified {
  const unconf = unconfirmedSignals(sentence);
  if (unconf.length) return { kind: "unconfirmed", attributed_to: "", signals: unconf.map((s) => `não confirmada: ${s}`) };
  const attr = attributionSignals(sentence);
  if (attr.length) {
    return { kind: "statement", attributed_to: attributedTo(sentence) || "autor da declaração por identificar",
      signals: attr.map((s) => `atribuída: ${s}`) };
  }
  const inf = inferenceSignals(sentence);
  if (inf.length) return { kind: "inference", attributed_to: "", signals: inf.map((s) => `inferência: ${s}`) };
  return { kind: "fact", attributed_to: "", signals: [] };
}

/** O que torna a frase verificável. */
export function checkableSignals(s: string): string[] {
  const out: string[] = [];
  if (new RegExp(PERCENT_RE.source, "giu").test(s)) out.push("percentagem");
  if (new RegExp(MONEY_RE.source, "giu").test(s)) out.push("valor monetário");
  if (quantities(s).some((q) => q.unit === "count")) out.push("número");
  if (new RegExp(DATE_RE.source, "giu").test(s)) out.push("data");
  const inst = institutions(s);
  if (inst.length) out.push(`instituição: ${inst.slice(0, 3).join(", ")}`);
  if (quotes(s).some((q) => q.text.split(/\s+/).length >= 4)) out.push("citação");
  if (unconfirmedSignals(s).length) out.push("marca de rumor ou de informação não confirmada");
  return out;
}

/** Frases verificáveis do título, subtítulo, resumo e texto (sem repetições). */
export function extractCheckable(text: { title: string; subtitle: string; summary: string; body: string }): string[] {
  const all = [text.title, text.subtitle, text.summary, ...paragraphs(plain(text.body))].flatMap((p) => sentences(p));
  const seen = new Set<string>();
  return all.filter((s) => {
    const k = fold(s).replace(/\s+/g, " ");
    if (seen.has(k) || !isCheckable(s) || checkableSignals(s).length === 0) return false;
    seen.add(k);
    return true;
  });
}

/** Possíveis contradições: a mesma entidade, a mesma unidade e métrica, valores diferentes em frases diferentes. */
export function contradictions(sents: string[]): Contradiction[] {
  const groups = new Map<string, { entity: string; unit: string; metric: string; vals: Map<string, string> }>();
  const years = (s: string) => [...s.matchAll(/\b(19|20)\d{2}\b/g)].map((m) => m[0]).sort().join(",");
  for (const s of sents) {
    for (const e of institutions(s)) {
      for (const q of quantities(s)) {
        if (!q.metric) continue;
        const key = `${fold(e)}|${q.unit}|${q.metric}|${years(s)}`;
        const g = groups.get(key) ?? { entity: e, unit: q.unit, metric: q.metric, vals: new Map() };
        if (!g.vals.has(String(q.value))) g.vals.set(String(q.value), s);
        groups.set(key, g);
      }
    }
  }
  const out: Contradiction[] = [];
  for (const g of groups.values()) {
    const sentencesUsed = [...new Set(g.vals.values())];
    if (g.vals.size > 1 && sentencesUsed.length > 1) {
      out.push({ entity: g.entity, unit: g.unit, metric: g.metric,
        values: [...g.vals.entries()].map(([v, s]) => quantities(s).find((q) => String(q.value) === v)?.raw ?? v),
        sentences: sentencesUsed });
    }
  }
  return out;
}

/** Referências da peça que mencionam termos da frase: documentos e dados são evidência CANDIDATA; artigos de outros meios são só repetição. */
function matchRefs(sentence: string, refs: RefRow[]): { evidence: Evidence[]; repetition: { url: string; title: string }[] } {
  const terms = [...quantities(sentence).map((q) => fold(q.raw.split(/\s+/)[0]!)), ...institutions(sentence).map(fold)];
  const key = titleKey(sentence);
  const evidence: Evidence[] = [], repetition: { url: string; title: string }[] = [];
  for (const r of refs) {
    const hay = fold(`${r.title} ${r.note} ${r.credit}`);
    const hit = terms.some((t) => t.length > 1 && hay.includes(t)) || similarity(key, titleKey(`${r.title} ${r.note}`)) >= 0.3;
    if (!hit) continue;
    if (r.kind === "article") repetition.push({ url: r.url, title: r.title });
    else evidence.push({ url: r.url, title: r.title, quote: "", relation: "candidate" });
  }
  return { evidence, repetition };
}

/** Evidência já registada numa afirmação (formato livre na base de dados): só entradas com endereço válido. */
function storedEvidence(v: unknown): Evidence[] {
  if (!Array.isArray(v)) return [];
  return v.flatMap((e) => {
    const o = e as Record<string, unknown>;
    if (typeof o?.url !== "string" || !/^https?:\/\/\S+$/i.test(o.url)) return [];
    return [{ url: o.url, title: typeof o.title === "string" ? o.title.slice(0, 500) : "",
      quote: typeof o.quote === "string" ? o.quote.slice(0, 2000) : "", relation: "cited" as const }];
  });
}

/** Verificação da peça: cria afirmações pendentes (sem duplicar) e devolve o relatório. */
export async function checkStory(ctx: Ctx, storyId: string, opts: AgentOpts = {}): Promise<AgentResult<FactcheckReport>> {
  const env = agentEnv(opts);
  const { story, refs, existing } = await withCtx(ctx, async (tx) => {
    const story = await storyFor(tx, ctx, storyId);
    return { story, refs: await loadRefs(tx, storyId), existing: await loadClaims(tx, storyId) };
  });

  const sents = extractCheckable(story);
  const planned = sents.map((s) => {
    const c = classify(s);
    const { evidence, repetition } = matchRefs(s, refs);
    const prior = existing.find((e) => fold(e.text).replace(/\s+/g, " ") === fold(s).replace(/\s+/g, " ")
      || similarity(titleKey(e.text), titleKey(s)) >= 0.85);
    return { text: clip(s, 1900), ...c, signals: [...checkableSignals(s), ...c.signals], evidence, repetition, prior };
  });

  // gravar só as novas, sempre pendentes; uma existente fica como está (o agente não reclassifica o trabalho humano)
  const claims: CheckedClaim[] = await withCtx(ctx, async (tx) => {
    const out: CheckedClaim[] = [];
    for (const p of planned) {
      if (p.prior) {
        const stored = storedEvidence(p.prior.evidence);
        const extra = p.evidence.filter((e) => !stored.some((s) => s.url === e.url));
        out.push({ text: p.prior.text, kind: p.prior.kind as ClaimKind, attributed_to: p.prior.attributed_to,
          evidence: [...stored, ...extra], claim_id: p.prior.id, created: false,
          verification: p.prior.verification as CheckedClaim["verification"], signals: p.signals, repetition: p.repetition });
        continue;
      }
      const [row] = await tx<{ id: string; verification: string }[]>`
        insert into claims (publication_id, story_id, text, kind, attributed_to, evidence, verification, in_article, origin)
        values (${ctx.publicationId}, ${story.id}, ${p.text}, ${p.kind}, ${p.attributed_to},
                ${tx.json(p.evidence as never)}, 'pending', false, 'agent')
        returning id, verification`;
      out.push({ text: p.text, kind: p.kind, attributed_to: p.attributed_to, evidence: p.evidence, claim_id: row!.id,
        created: true, verification: "pending", signals: p.signals, repetition: p.repetition });
    }
    return out;
  });

  // passo opcional: segunda opinião do modelo sobre a classificação (só no relatório; não muda afirmações)
  const known = new Set(claims.map((c) => fold(c.text).replace(/\s+/g, " ")));
  const step = await llmJson<{ claims: LlmClaimOpinion[] }>(env,
    [
      "Tarefa: classificar cada frase verificável em fact | statement | inference | unconfirmed.",
      "statement exige `attributed_to` (quem declarou, tal como está no texto). Na dúvida, usa o tipo mais prudente.",
      "`text` tem de ser a frase tal como está numerada no material. Explica em `note` porquê (uma frase).",
      'Formato: {"claims":[{"text":"...","kind":"...","attributed_to":"...","note":"..."}]}',
      material(claims.map((c) => c.text)),
    ].join("\n"),
    (v) => {
      const r = check<{ claims: LlmClaimOpinion[] }>(llmShapes.claimOpinions, v);
      if (!r.ok) return r;
      const errs: string[] = [];
      for (const c of r.value.claims) {
        if (!known.has(fold(c.text).replace(/\s+/g, " "))) errs.push("frase que não está no material");
        if (c.kind === "statement" && !c.attributed_to.trim()) errs.push("declaração sem autor");
      }
      return errs.length ? { ok: false, errors: errs } : r;
    });

  const counts = { fact: 0, statement: 0, inference: 0, unconfirmed: 0 };
  for (const c of claims) counts[c.kind]++;
  const output: FactcheckReport = {
    ...envelope<"factcheck_report">(AGENT_ID, env,
      { story_id: story.id, story_version: story.version, refs: refs.length, existing_claims: existing.length, sentences: sents.length },
      [...claims.flatMap((c) => c.evidence.map((e) => e.url)), ...claims.flatMap((c) => c.repetition.map((r) => r.url))],
      step.info, ["Nenhuma afirmação foi marcada como verificada: a verificação é de uma pessoa."]),
    story: { id: story.id, version: story.version, state: story.state },
    claims,
    counts,
    contradictions: contradictions([...sents, ...existing.map((e) => e.text)]),
    rules: RULES,
    second_opinion: step.value?.claims ?? [],
  };
  const created = claims.filter((c) => c.created).length;
  const note = `Verificação automática: ${claims.length} frase(s) verificável(eis), ${created} afirmação(ões) nova(s) pendente(s)`
    + `, ${counts.unconfirmed} não confirmada(s), ${output.contradictions.length} possível(eis) contradição(ões). Nada foi dado como verificado.`;
  return { output, note, llm: step.info };
}
