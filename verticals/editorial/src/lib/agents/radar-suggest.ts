/**
 * Radar (`editorial.radar`). Agrupa os itens recentes do radar que são a mesma história (duplicados e
 * títulos semelhantes), ordena os grupos por relevância × número de meios diferentes × actualidade e propõe
 * os melhores como sugestões de pauta. Só cria ideias (estado `idea`, origem agente) se lhe pedirem.
 */
import type { Ctx } from "../context";
import { withCtx } from "../db";
import { similarity, titleKey } from "../text";
import { check, type Cluster, llmShapes, type StorySuggestions } from "./contracts";
import { llmJson, material } from "./llm";
import { type AgentOpts, type AgentResult, AgentError, agentEnv, envelope } from "./shared";
import { clip, fold } from "./textkit";

export const AGENT_ID = "editorial.radar" as const;

export interface RadarOpts extends AgentOpts {
  topN?: number;
  windowHours?: number;
  /** Só com `true` o agente cria ideias de peça para os melhores grupos. */
  createIdeas?: boolean;
  /** Semelhança mínima de títulos para juntar dois itens (0 a 1). */
  minSimilarity?: number;
}

export interface RadarItem {
  id: string; url: string; title: string; title_key: string; published_at: Date | null; fetched_at: Date;
  duplicate_of: string | null; relevance: number; topics: string[];
  source_id: string; source_name: string; tier: "primary" | "institutional" | "media"; category: string;
}
interface Section { id: string; slug: string; name: string }

const TIER_RANK = { primary: 0, institutional: 1, media: 2 } as const;

/** Agrupa itens: um duplicado junta-se ao original; títulos semelhantes (ou parecidos e com tema comum) juntam-se. */
export function clusterItems(items: RadarItem[], minSim = 0.5): RadarItem[][] {
  const byId = new Map(items.map((i) => [i.id, i]));
  const parent = new Map(items.map((i) => [i.id, i.id]));
  const find = (x: string): string => { let r = x; while (parent.get(r) !== r) r = parent.get(r)!; parent.set(x, r); return r; };
  const union = (a: string, b: string) => { const ra = find(a), rb = find(b); if (ra !== rb) parent.set(rb, ra); };
  for (const i of items) if (i.duplicate_of && byId.has(i.duplicate_of)) union(i.duplicate_of, i.id);
  const keys = items.map((i) => i.title_key || titleKey(i.title));
  for (let a = 0; a < items.length; a++) {
    for (let b = a + 1; b < items.length; b++) {
      const sim = similarity(keys[a]!, keys[b]!);
      const shared = items[a]!.topics.some((t) => items[b]!.topics.includes(t));
      if (sim >= minSim || (shared && sim >= minSim * 0.6)) union(items[a]!.id, items[b]!.id);
    }
  }
  const groups = new Map<string, RadarItem[]>();
  for (const i of items) { const r = find(i.id); groups.set(r, [...(groups.get(r) ?? []), i]); }
  return [...groups.values()];
}

/** Pontuação: (1 + relevância máxima) × meios diferentes × actualidade (1 / (1 + horas/24)). */
export function scoreCluster(group: RadarItem[], now: Date): number {
  const rel = Math.max(...group.map((i) => i.relevance));
  const sources = new Set(group.map((i) => i.source_id)).size;
  const latest = Math.max(...group.map((i) => (i.published_at ?? i.fetched_at).getTime()));
  const hours = Math.max(0, (now.getTime() - latest) / 3_600_000);
  return Math.round((1 + Math.max(0, rel)) * sources * (1 / (1 + hours / 24)) * 1000) / 1000;
}

function sectionFor(group: RadarItem[], sections: Section[]): Section | null {
  const hints = group.flatMap((i) => [...i.topics, i.category]).filter(Boolean).map(fold);
  for (const s of sections) {
    if (hints.some((h) => h === fold(s.slug) || h === fold(s.name) || h.includes(fold(s.name)))) return s;
  }
  return null;
}

export async function suggestFromRadar(ctx: Ctx, publicationId: string, opts: RadarOpts = {}): Promise<AgentResult<StorySuggestions>> {
  if (ctx.kind !== "agent") throw new AgentError("os agentes correm sempre com contexto de agente");
  if (ctx.publicationId !== publicationId) throw new AgentError("o contexto não é desta publicação");
  const env = agentEnv(opts);
  const topN = Math.min(Math.max(opts.topN ?? 5, 1), 50);
  const windowHours = opts.windowHours ?? 72;
  const since = new Date(env.now.getTime() - windowHours * 3_600_000);

  const { items, sections } = await withCtx(ctx, async (tx) => {
    const items = await tx<RadarItem[]>`
      select fi.id, fi.url, fi.title, fi.title_key, fi.published_at, fi.fetched_at, fi.duplicate_of, fi.relevance, fi.topics,
             fs.id as source_id, fs.name as source_name, fs.tier, fs.category
      from feed_items fi join feed_sources fs on fs.id = fi.feed_source_id
      where fi.status = 'new' and coalesce(fi.published_at, fi.fetched_at) >= ${since}
      order by coalesce(fi.published_at, fi.fetched_at) desc limit 1000`;
    const sections = await tx<Section[]>`select id, slug, name from sections where active order by position, name`;
    return { items, sections };
  });

  const ranked = clusterItems(items, opts.minSimilarity ?? 0.5)
    // um grupo começa num item original: duplicados soltos (o original já não está «novo») não abrem grupo
    .filter((g) => g.some((i) => !i.duplicate_of || !items.some((x) => x.id === i.duplicate_of)))
    .map((g) => ({ g, score: scoreCluster(g, env.now) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topN);

  let clusters: Cluster[] = ranked.map(({ g, score }) => {
    const lead = [...g].sort((a, b) => TIER_RANK[a.tier] - TIER_RANK[b.tier] || b.relevance - a.relevance
      || (a.published_at ?? a.fetched_at).getTime() - (b.published_at ?? b.fetched_at).getTime())[0]!;
    const sources = [...new Set(g.map((i) => i.source_name))];
    const topics = [...new Set(g.flatMap((i) => i.topics))].slice(0, 10);
    const latest = new Date(Math.max(...g.map((i) => (i.published_at ?? i.fetched_at).getTime())));
    const section = sectionFor(g, sections);
    const why = [
      `${sources.length} meio(s) diferente(s): ${clip(sources.join(", "), 300)}.`,
      g.some((i) => i.tier !== "media") ? "Há fonte primária ou institucional no grupo." : "Só fontes mediáticas: procurar a fonte original.",
      topics.length ? `Temas: ${topics.slice(0, 5).join(", ")}.` : "",
      "A repetição entre meios indica interesse, não confirma factos.",
    ].filter(Boolean).join(" ");
    return {
      title: clip(lead.title, 480), why, item_ids: g.map((i) => i.id), item_urls: [...new Set(g.map((i) => i.url))],
      sources, sources_count: new Set(g.map((i) => i.source_id)).size, topics,
      latest_at: latest.toISOString(), score, suggested_section: section?.name ?? null, suggested_section_id: section?.id ?? null,
      idea_story_id: null, proposed_title: null, proposed_angle: null,
    };
  });

  // passo opcional: título e ângulo neutros por grupo, só a partir dos títulos fornecidos
  const step = clusters.length === 0
    ? { value: null, info: { status: "skipped" as const, model: env.llm?.model ?? "", reason: "sem grupos para sugerir" } }
    : await llmJson<{ clusters: { n: number; title: string; angle: string }[] }>(env,
      [
        "Tarefa: para cada grupo numerado de títulos (a mesma história em vários meios), propõe um título neutro e um ângulo de pauta.",
        "Sem adjectivos sensacionalistas. Não acrescentes factos que não estejam nos títulos.",
        'Formato: {"clusters":[{"n":1,"title":"...","angle":"..."}]}',
        material(ranked.map((r) => r.g.map((i) => i.title).join(" | "))),
      ].join("\n"),
      (v) => {
        const r = check<{ clusters: { n: number; title: string; angle: string }[] }>(llmShapes.clusterTitles, v);
        if (!r.ok) return r;
        const bad = r.value.clusters.filter((c) => !Number.isInteger(c.n) || c.n < 1 || c.n > clusters.length || /https?:\/\//.test(c.title + c.angle));
        return bad.length ? { ok: false, errors: ["grupo inexistente ou endereço inventado"] } : r;
      });
  if (step.value) {
    for (const c of step.value.clusters) {
      const target = clusters[c.n - 1]!;
      target.proposed_title = c.title;
      target.proposed_angle = c.angle;
    }
  }

  // ideias de peça: só quando pedido, nunca repetidas, com as ligações como referências
  if (opts.createIdeas) {
    clusters = await withCtx(ctx, async (tx) => {
      const out: Cluster[] = [];
      for (const c of clusters) {
        const [dup] = await tx<{ id: string }[]>`
          select id from stories where origin = 'agent' and title = ${c.title} and created_at > now() - interval '14 days' limit 1`;
        if (dup) { out.push({ ...c, idea_story_id: dup.id }); continue; }
        const [s] = await tx<{ id: string }[]>`
          insert into stories (publication_id, section_id, state, origin, title, angle, to_confirm)
          values (${publicationId}, ${c.suggested_section_id}, 'idea', 'agent', ${c.title},
                  ${clip(`Sugestão do radar. ${c.why}`, 2000)},
                  ${"Confirmar em fonte primária antes de avançar: os itens do radar são de outros meios."})
          returning id`;
        for (const url of c.item_urls.slice(0, 20)) {
          const src = c.sources.join(", ");
          await tx`insert into story_refs (publication_id, story_id, kind, url, title, credit, note, added_kind)
                   values (${publicationId}, ${s!.id}, 'article', ${url}, ${c.title}, ${clip(src, 200)}, 'Do radar', 'agent')`;
        }
        out.push({ ...c, idea_story_id: s!.id });
      }
      return out;
    }, "sugestão do radar");
  }

  const output: StorySuggestions = {
    ...envelope<"story_suggestions">(AGENT_ID, env,
      { publication_id: publicationId, window_hours: windowHours, top_n: topN, create_ideas: Boolean(opts.createIdeas), items: items.length },
      clusters.flatMap((c) => c.item_urls), step.info,
      opts.createIdeas ? ["Foram criadas ideias de peça (estado «ideia») para os grupos sugeridos."] : []),
    window_hours: windowHours,
    items_considered: items.length,
    clusters,
  };
  return { output, llm: step.info };
}
