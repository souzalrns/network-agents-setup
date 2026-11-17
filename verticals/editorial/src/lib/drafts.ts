import { diffWords } from "diff";
import type { Ctx } from "./context";
import { type Tx, withCtx } from "./db";
import { isHttpUrl } from "./forms";
import { EditorialError, getStory, type Story, type StoryPatch, updateStory } from "./stories";

/**
 * Rascunhos no servidor, versões e conflitos (D4).
 * - O autosave grava `story_drafts` (um por peça) sem criar versões; cada gravação traz o `rev` que o
 *   browser conhece: se outra pessoa gravou no meio, é conflito e nada se perde (devolve-se o rascunho dela).
 * - «Guardar versão» promove o rascunho a versão da peça com `expectedVersion`: se a peça mudou entretanto,
 *   é conflito (a última gravação já não ganha em silêncio).
 * - Restaurar uma versão cria uma versão nova; o histórico nunca é reescrito.
 */

export const ARTICLE_KEYS = ["title", "subtitle", "summary", "body", "slug", "hero_image_url", "hero_caption", "hero_credit",
  "tags", "seo_title", "meta_description", "kind"] as const;
export type ArticleKey = (typeof ARTICLE_KEYS)[number];
export type ArticleFields = { [K in ArticleKey]: K extends "tags" ? string[] : K extends "hero_image_url" | "slug" ? string | null : string };

const LIMITS: Record<string, number> = { title: 300, subtitle: 600, summary: 1200, body: 200_000, slug: 120, hero_image_url: 1000,
  hero_caption: 600, hero_credit: 200, seo_title: 120, meta_description: 320, kind: 20 };
export const KINDS = ["news", "opinion", "interview", "sponsored"];
export const LEASE_SECONDS = 120;

export class ConflictError extends EditorialError {
  constructor(message: string, readonly current?: unknown) { super(message); }
}

/** Campos do artigo a partir de um formulário ou de JSON, com limites e tipos. Nada passa sem isto. */
export function parseArticle(get: (k: string) => unknown): ArticleFields {
  const s = (k: string) => String(get(k) ?? "").slice(0, LIMITS[k] ?? 1000).trim();
  const tagsRaw = get("tags");
  const tags = (Array.isArray(tagsRaw) ? tagsRaw.map(String) : String(tagsRaw ?? "").split(","))
    .map((t) => t.trim().toLowerCase().slice(0, 40)).filter(Boolean).slice(0, 12);
  const hero = s("hero_image_url");
  if (hero && !isHttpUrl(hero)) throw new EditorialError("O endereço da imagem tem de começar por https://.");
  const kind = s("kind");
  return {
    title: s("title"), subtitle: s("subtitle"), summary: s("summary"), body: String(get("body") ?? "").slice(0, LIMITS.body),
    slug: s("slug") || null, hero_image_url: hero || null, hero_caption: s("hero_caption"), hero_credit: s("hero_credit"),
    tags, seo_title: s("seo_title"), meta_description: s("meta_description"), kind: KINDS.includes(kind) ? kind : "news",
  };
}

export const articleOf = (s: Story): ArticleFields => ({
  title: s.title, subtitle: s.subtitle, summary: s.summary, body: s.body, slug: s.slug, hero_image_url: s.hero_image_url,
  hero_caption: s.hero_caption, hero_credit: s.hero_credit, tags: s.tags, seo_title: s.seo_title,
  meta_description: s.meta_description, kind: s.kind,
});

export interface Draft {
  story_id: string; base_version: number; rev: number; fields: ArticleFields; updated_by: string | null; updated_at: Date;
  by_name: string | null; lease_user: string | null; lease_until: Date | null; lease_name: string | null;
}

export async function getDraft(tx: Tx, storyId: string): Promise<Draft | null> {
  const [d] = await tx<Draft[]>`select d.story_id, d.base_version, d.rev, d.fields, d.updated_by, d.updated_at, d.lease_user, d.lease_until,
      mu.display_name as by_name, ml.display_name as lease_name
    from story_drafts d
    left join memberships mu on mu.user_id = d.updated_by and mu.publication_id = d.publication_id
    left join memberships ml on ml.user_id = d.lease_user and ml.publication_id = d.publication_id
    where d.story_id = ${storyId}`;
  return d ?? null;
}

export type SaveResult =
  | { status: "saved"; rev: number; updated_at: Date }
  | { status: "conflict"; reason: "draft" | "version"; draft: Draft | null; version: number };

/**
 * Autosave. `rev` é a revisão do rascunho que o browser tem (null se ainda não tem nenhum);
 * `baseVersion` é a versão da peça sobre a qual está a escrever. `force` sobrepõe o rascunho de outra pessoa
 * (decisão explícita de quem vê o conflito), nunca uma versão já guardada.
 */
export async function saveDraft(ctx: Ctx, storyId: string, input: { rev: number | null; baseVersion: number; fields: ArticleFields; force?: boolean }): Promise<SaveResult> {
  return withCtx(ctx, async (tx) => {
    const [story] = await tx<{ version: number }[]>`select version from stories where id = ${storyId}`;
    if (!story) throw new EditorialError("Não encontrei a peça.");
    const [cur] = await tx<{ rev: number; base_version: number }[]>`select rev, base_version from story_drafts where story_id = ${storyId} for update`;
    if (story.version !== input.baseVersion && !(cur && cur.base_version === input.baseVersion && input.force)) {
      return { status: "conflict", reason: "version", draft: await getDraft(tx, storyId), version: story.version };
    }
    if (cur && cur.rev !== input.rev && !input.force) {
      return { status: "conflict", reason: "draft", draft: await getDraft(tx, storyId), version: story.version };
    }
    const lease = new Date(Date.now() + LEASE_SECONDS * 1000);
    const rows = cur
      ? await tx<{ rev: number; updated_at: Date }[]>`update story_drafts set fields = ${tx.json(input.fields as never)}, base_version = ${input.baseVersion},
          updated_by = ${ctx.userId!}, lease_user = ${ctx.userId!}, lease_until = ${lease} where story_id = ${storyId} returning rev, updated_at`
      : await tx<{ rev: number; updated_at: Date }[]>`insert into story_drafts (story_id, publication_id, base_version, fields, updated_by, lease_user, lease_until)
          values (${storyId}, ${ctx.publicationId}, ${input.baseVersion}, ${tx.json(input.fields as never)}, ${ctx.userId!}, ${ctx.userId!}, ${lease})
          returning rev, updated_at`;
    if (!rows.length) throw new EditorialError("Não tens permissão para editar esta peça.");
    return { status: "saved", rev: rows[0]!.rev, updated_at: rows[0]!.updated_at };
  });
}

export async function discardDraft(ctx: Ctx, storyId: string): Promise<void> {
  await withCtx(ctx, (tx) => tx`delete from story_drafts where story_id = ${storyId}`);
}

/** Diferença entre o que está guardado e o que vem: só os campos que mudam (para não criar versões vazias). */
export function changedFields(before: ArticleFields, after: ArticleFields): StoryPatch {
  const patch: Record<string, unknown> = {};
  for (const k of ARTICLE_KEYS) {
    const a = before[k], b = after[k];
    if (JSON.stringify(a ?? null) !== JSON.stringify(b ?? null)) patch[k] = b;
  }
  return patch as StoryPatch;
}

/**
 * Guarda uma versão: grava os campos na peça se ela ainda estiver na versão em que o texto foi começado,
 * e apaga o rascunho. Se outra pessoa guardou entretanto, recusa com ConflictError.
 */
export async function saveVersion(ctx: Ctx, storyId: string, fields: ArticleFields, expectedVersion: number, note = ""): Promise<Story> {
  const current = await withCtx(ctx, (tx) => getStory(tx, storyId));
  if (!current) throw new EditorialError("Não encontrei a peça.");
  if (current.version !== expectedVersion) {
    throw new ConflictError(`Outra pessoa guardou a versão ${current.version} enquanto escrevias (começaste na ${expectedVersion}). O teu texto ficou no rascunho: compara e junta antes de guardar.`);
  }
  const patch = changedFields(articleOf(current), fields);
  if (!Object.keys(patch).length) { await discardDraft(ctx, storyId); return current; }
  const saved = await updateStory(ctx, storyId, patch, note, expectedVersion);
  await discardDraft(ctx, storyId);
  return saved;
}

export interface VersionRow { version: number; title: string; subtitle: string; summary: string; body: string; snapshot: Partial<ArticleFields> | null;
  saved_at: Date; saved_kind: string; note: string; name: string | null }

export async function getVersion(tx: Tx, storyId: string, version: number): Promise<VersionRow | null> {
  const [v] = await tx<VersionRow[]>`select v.version, v.title, v.subtitle, v.summary, v.body, v.snapshot, v.saved_at, v.saved_kind, v.note,
      m.display_name as name from story_versions v left join memberships m on m.user_id = v.saved_by and m.publication_id = v.publication_id
    where v.story_id = ${storyId} and v.version = ${version}`;
  return v ?? null;
}

/** Campos de uma versão: o retrato completo quando existe; nas versões antigas só os textos. */
export function fieldsOfVersion(v: VersionRow, fallback: ArticleFields): ArticleFields {
  const snap = v.snapshot ?? {};
  return { ...fallback, ...snap, title: v.title, subtitle: v.subtitle, summary: v.summary, body: v.body } as ArticleFields;
}

/** Restaurar cria uma versão nova com o conteúdo antigo (fica registado de onde veio). */
export async function restoreVersion(ctx: Ctx, storyId: string, version: number, expectedVersion: number): Promise<Story> {
  const { current, old } = await withCtx(ctx, async (tx) => {
    return { current: await getStory(tx, storyId), old: await getVersion(tx, storyId, version) };
  });
  if (!current || !old) throw new EditorialError("Não encontrei essa versão.");
  if (current.version !== expectedVersion) throw new ConflictError(`A peça mudou para a versão ${current.version} entretanto. Revê antes de restaurar.`);
  const fields = fieldsOfVersion(old, articleOf(current));
  const patch = changedFields(articleOf(current), fields);
  if (!Object.keys(patch).length) throw new EditorialError("Essa versão é igual à actual.");
  return updateStory(ctx, storyId, patch, `Restaurada a versão ${version}`, expectedVersion);
}

export type DiffPart = { value: string; added?: boolean; removed?: boolean };
export interface FieldDiff { key: ArticleKey; parts: DiffPart[]; changed: boolean }

/** Comparação palavra a palavra, campo a campo. */
export function compareArticles(a: ArticleFields, b: ArticleFields): FieldDiff[] {
  return ARTICLE_KEYS.map((key) => {
    const x = key === "tags" ? (a.tags ?? []).join(", ") : String(a[key] ?? "");
    const y = key === "tags" ? (b.tags ?? []).join(", ") : String(b[key] ?? "");
    const parts = x === y ? [{ value: x }] : diffWords(x, y).map((p) => ({ value: p.value, added: p.added, removed: p.removed }));
    return { key, parts, changed: x !== y };
  });
}
