import { canWrite, type Ctx, systemCtx } from "../context";
import { db, withCtx } from "../db";
import { createStory, EditorialError, type Story } from "../stories";
import { excerpt, similarity, titleKey, urlKey } from "../text";
import { FeedError, parseFeed } from "./feed";
import { type FetchImpl, type Resolver, safeFetch } from "./fetch";
import { DEFAULT_TOPICS, scoreItem, type Tier, type TopicRule } from "./score";

/**
 * Radar: vai buscar os feeds das fontes activas, normaliza, deduplica, pontua e guarda só metadados e um excerto.
 * Corre como `system` (a base de dados só deixa o sistema inserir entradas do radar). Uma fonte com problemas
 * fica marcada (erro ou bloqueada) e não impede as outras.
 */

export const NEAR_DUPLICATE = 0.6;
export const NEAR_DUPLICATE_WINDOW_HOURS = 72;
const ERROR_MAX = 500;

export interface RadarOpts {
  /** Fontes a correr já, mesmo que o intervalo ainda não tenha passado (as inactivas continuam de fora). */
  sourceIds?: string[];
  allowlist?: readonly string[];
  fetchImpl?: FetchImpl;
  resolve?: Resolver;
  topics?: readonly TopicRule[];
  timeoutMs?: number;
  maxBytes?: number;
}

export type SourceStatus = "ok" | "not_modified" | "error" | "blocked";

export interface SourceSummary {
  sourceId: string;
  name: string;
  status: SourceStatus;
  /** Entradas lidas no feed. */
  entries: number;
  inserted: number;
  /** Inseridas mas marcadas como a mesma notícia de outra entrada recente (`duplicate_of`). */
  nearDuplicates: number;
  /** Já existiam (mesmo endereço) ou eram inválidas. */
  skipped: number;
  error?: string;
}

export interface RadarSummary {
  publicationId: string;
  startedAt: Date;
  finishedAt: Date;
  sources: SourceSummary[];
}

interface SourceRow {
  id: string; name: string; feed_url: string; tier: Tier; etag: string | null; last_modified: string | null;
}

interface Recent { id: string; title_key: string; duplicate_of: string | null }

const clip = (s: string) => s.slice(0, ERROR_MAX);

/** Corre o radar de uma publicação e devolve o resumo por fonte. */
export async function runRadar(publicationId: string, opts: RadarOpts = {}): Promise<RadarSummary> {
  const ctx = systemCtx(publicationId, "radar");
  const startedAt = new Date();
  const forced = opts.sourceIds?.length ? opts.sourceIds : null;
  const sources = await withCtx(ctx, (tx) => tx<SourceRow[]>`
    select id, name, feed_url, tier, etag, last_modified from feed_sources
    where active and ${forced
      ? tx`id = any(${forced}::uuid[])`
      : tx`(last_fetched_at is null or last_fetched_at + make_interval(mins => interval_minutes) <= now())`}
    order by last_fetched_at nulls first, name`);

  const summaries: SourceSummary[] = [];
  for (const src of sources) {
    let summary: SourceSummary;
    try {
      summary = await runSource(ctx, src, opts);
    } catch (e) {
      // falha inesperada (ex.: base de dados): regista-se na fonte e segue-se para a próxima
      summary = { sourceId: src.id, name: src.name, status: "error", entries: 0, inserted: 0, nearDuplicates: 0, skipped: 0,
        error: clip(`Erro inesperado: ${(e as Error).message}`) };
      await markSource(ctx, src.id, "error", summary.error!, src.etag, src.last_modified).catch(() => {});
    }
    summaries.push(summary);
  }
  return { publicationId, startedAt, finishedAt: new Date(), sources: summaries };
}

/** Corre o radar em todas as publicações (tarefa agendada). */
export async function runRadarAll(opts: Omit<RadarOpts, "sourceIds"> = {}): Promise<RadarSummary[]> {
  const pubs = await db()<{ id: string }[]>`select id from editorial.system_publications()`;
  const out: RadarSummary[] = [];
  for (const p of pubs) out.push(await runRadar(p.id, opts));
  return out;
}

async function markSource(ctx: Ctx, id: string, status: SourceStatus, error: string, etag: string | null, lastModified: string | null) {
  await withCtx(ctx, (tx) => tx`
    update feed_sources set last_fetched_at = now(), last_status = ${status}, last_error = ${clip(error)},
      etag = ${etag}, last_modified = ${lastModified}
    where id = ${id}`);
}

async function runSource(ctx: Ctx, src: SourceRow, opts: RadarOpts): Promise<SourceSummary> {
  const base: SourceSummary = { sourceId: src.id, name: src.name, status: "ok", entries: 0, inserted: 0, nearDuplicates: 0, skipped: 0 };
  const res = await safeFetch(src.feed_url, {
    allowlist: opts.allowlist, fetchImpl: opts.fetchImpl, resolve: opts.resolve, timeoutMs: opts.timeoutMs,
    maxBytes: opts.maxBytes, etag: src.etag, lastModified: src.last_modified,
  });

  if (res.kind === "not_modified") {
    await markSource(ctx, src.id, "not_modified", "", res.etag, res.lastModified);
    return { ...base, status: "not_modified" };
  }
  if (res.kind === "blocked" || res.kind === "error") {
    // num erro mantêm-se os validadores anteriores: o próximo pedido continua condicional
    await markSource(ctx, src.id, res.kind, res.message, src.etag, src.last_modified);
    return { ...base, status: res.kind, error: res.message };
  }

  let entries;
  try {
    entries = parseFeed(res.body, res.url).entries;
  } catch (e) {
    const msg = e instanceof FeedError ? e.message : `Feed ilegível: ${(e as Error).message}`;
    await markSource(ctx, src.id, "error", msg, src.etag, src.last_modified);
    return { ...base, status: "error", error: clip(msg) };
  }

  const topics = opts.topics ?? DEFAULT_TOPICS;
  return withCtx(ctx, async (tx) => {
    const recent = await tx<Recent[]>`
      select id, title_key, duplicate_of from feed_items
      where fetched_at > now() - make_interval(hours => ${NEAR_DUPLICATE_WINDOW_HOURS}) and title_key <> ''
      order by fetched_at, id`;
    const out = { ...base, entries: entries.length };
    for (const e of entries) {
      const key = urlKey(e.url);
      const tkey = titleKey(e.title);
      if (!key) { out.skipped++; continue; }
      const text = excerpt(e.summaryHtml, 300);
      const score = scoreItem({ title: e.title, excerpt: text, tier: src.tier }, topics);
      const dup = nearestDuplicate(tkey, recent);
      const [row] = await tx<{ id: string }[]>`
        insert into feed_items (publication_id, feed_source_id, url, url_key, title, title_key, excerpt, published_at,
          duplicate_of, relevance, topics)
        values (${ctx.publicationId}, ${src.id}, ${e.url}, ${key}, ${e.title}, ${tkey}, ${text}, ${e.publishedAt},
          ${dup}, ${score.relevance}, ${score.topics})
        on conflict (publication_id, url_key) do nothing
        returning id`;
      if (!row) { out.skipped++; continue; }
      out.inserted++;
      if (dup) out.nearDuplicates++;
      if (tkey) recent.push({ id: row.id, title_key: tkey, duplicate_of: dup });
    }
    await tx`
      update feed_sources set last_fetched_at = now(), last_status = 'ok', last_error = '',
        etag = ${res.etag}, last_modified = ${res.lastModified}
      where id = ${src.id}`;
    return out;
  });
}

/** A entrada recente mais parecida (≥ limiar); aponta sempre para a original, nunca para outra cópia. */
function nearestDuplicate(tkey: string, recent: Recent[]): string | null {
  if (!tkey) return null;
  let best: Recent | null = null;
  let bestScore = 0;
  for (const r of recent) {
    const s = similarity(tkey, r.title_key);
    if (s >= NEAR_DUPLICATE && s > bestScore) { best = r; bestScore = s; } // em empate fica a mais antiga
  }
  return best ? best.duplicate_of ?? best.id : null;
}

// ---------------------------------------------------------------- acções da redacção sobre uma entrada

interface ItemRow { id: string; title: string; url: string; excerpt: string; status: string; story_id: string | null }

function assertCanAct(ctx: Ctx) {
  if (ctx.kind === "system") return;
  if (ctx.kind === "human" && canWrite(ctx.role)) return;
  throw new EditorialError("Só a redacção (ou o próprio radar) trata as entradas do radar.");
}

/**
 * Transforma uma entrada do radar numa ideia de pauta (estado `idea`): origem `radar` se for o sistema,
 * em nome da pessoa se for alguém da redacção. A entrada fica `linked` à peça criada.
 */
export async function promoteToIdea(ctx: Ctx, itemId: string): Promise<{ story: Story; itemId: string }> {
  assertCanAct(ctx);
  const item = await withCtx(ctx, async (tx) => {
    const [row] = await tx<ItemRow[]>`select id, title, url, excerpt, status, story_id from feed_items where id = ${itemId}`;
    return row;
  });
  if (!item) throw new EditorialError("Não encontrei esta entrada do radar.");
  if (item.status === "linked") throw new EditorialError("Esta entrada já deu origem a uma pauta.");

  const angle = [`Ver: ${item.url}`, item.excerpt].filter(Boolean).join("\n\n");
  const story = await createStory(ctx, { title: item.title, angle });
  const linked = await withCtx(ctx, (tx) => tx`
    update feed_items set status = 'linked', story_id = ${story.id}
    where id = ${itemId} and status <> 'linked' returning id`);
  if (!linked.length) throw new EditorialError("Esta entrada foi tratada entretanto por outra pessoa.");
  return { story, itemId };
}

/** Põe de lado uma entrada nova do radar. */
export async function dismissItem(ctx: Ctx, itemId: string): Promise<void> {
  assertCanAct(ctx);
  const rows = await withCtx(ctx, (tx) => tx`
    update feed_items set status = 'dismissed' where id = ${itemId} and status = 'new' returning id`);
  if (!rows.length) throw new EditorialError("Não encontrei esta entrada do radar ou ela já foi tratada.");
}
