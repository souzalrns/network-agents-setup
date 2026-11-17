import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { cache } from "react";
import type { Ctx } from "./context";
import { withCtx } from "./db";
import { type Publication, publicContext } from "./publication";

export interface PublicSection { id: string; slug: string; name: string; color: string; description: string }
export interface PublicStory {
  id: string; slug: string; title: string; subtitle: string; summary: string; body: string; kind: string; tags: string[];
  hero_image_url: string | null; hero_caption: string; hero_credit: string; seo_title: string; meta_description: string;
  published_at: Date; updated_at: Date; section_slug: string | null; section_name: string | null; section_color: string | null;
  author_name: string | null; author_slug: string | null; author_public: boolean | null;
}

/** Publicação e contexto público do pedido actual (por domínio). Sem publicação, 404. */
export const site = cache(async (): Promise<{ ctx: Ctx; pub: Publication; sections: PublicSection[]; baseUrl: string }> => {
  const h = await headers();
  const host = h.get("x-forwarded-host") ?? h.get("host");
  const ctx = await publicContext(host);
  if (!ctx) notFound();
  return withCtx(ctx, async (tx) => {
    const [pub] = await tx<Publication[]>`select * from publications where id = ${ctx.publicationId}`;
    const sections = await tx<PublicSection[]>`select id, slug, name, color, description from sections where active order by position, name`;
    const proto = h.get("x-forwarded-proto") ?? (host?.startsWith("localhost") ? "http" : "https");
    const baseUrl = process.env.EDITORIAL_SITE_URL ?? (pub!.domain ? `https://${pub!.domain}` : `${proto}://${host}`);
    return { ctx, pub: pub!, sections, baseUrl: baseUrl.replace(/\/+$/, "") };
  });
});

const COLS = `s.id, s.slug, s.title, s.subtitle, s.summary, s.body, s.kind, s.tags, s.hero_image_url, s.hero_caption, s.hero_credit,
  s.seo_title, s.meta_description, s.published_at, s.updated_at, sec.slug as section_slug, sec.name as section_name, sec.color as section_color,
  m.display_name as author_name, m.author_slug, m.public_profile as author_public`;
const FROM = `from stories s left join sections sec on sec.id = s.section_id
  left join memberships m on m.user_id = s.author_id and m.publication_id = s.publication_id`;

export async function latest(ctx: Ctx, opts: { section?: string; author?: string; limit?: number; offset?: number } = {}): Promise<PublicStory[]> {
  return withCtx(ctx, (tx) => {
    const v: unknown[] = [];
    const where = ["s.state = 'published'"];
    if (opts.section) { v.push(opts.section); where.push(`sec.slug = $${v.length}`); }
    if (opts.author) { v.push(opts.author); where.push(`m.author_slug = $${v.length} and m.public_profile`); }
    v.push(Math.min(opts.limit ?? 20, 100)); const lim = v.length;
    v.push(Math.max(opts.offset ?? 0, 0));
    return tx.unsafe<PublicStory[]>(`select ${COLS} ${FROM} where ${where.join(" and ")} order by s.published_at desc limit $${lim} offset $${v.length}`, v as never[]);
  });
}

export async function article(ctx: Ctx, slug: string) {
  return withCtx(ctx, async (tx) => {
    const [story] = await tx.unsafe<PublicStory[]>(`select ${COLS} ${FROM} where s.state = 'published' and s.slug = $1`, [slug]);
    if (!story) return null;
    const corrections = await tx<{ text: string; created_at: Date }[]>`select text, created_at from corrections where story_id = ${story.id} order by created_at`;
    const refs = await tx<{ url: string; title: string; kind: string }[]>`select url, title, kind from story_refs where story_id = ${story.id} order by created_at`;
    const related = await tx.unsafe<PublicStory[]>(`select ${COLS} ${FROM} where s.state = 'published' and s.id <> $1
      and s.section_id is not distinct from (select section_id from stories where id = $1) order by s.published_at desc limit 3`, [story.id]);
    return { story, corrections, refs, related };
  });
}

export async function author(ctx: Ctx, slug: string) {
  return withCtx(ctx, async (tx) => {
    const [a] = await tx<{ name: string; bio: string; author_slug: string }[]>`
      select display_name as name, bio, author_slug from memberships where author_slug = ${slug} and public_profile`;
    return a ?? null;
  });
}

export async function search(ctx: Ctx, q: string): Promise<PublicStory[]> {
  if (!q.trim()) return [];
  return withCtx(ctx, (tx) => tx.unsafe<PublicStory[]>(`select ${COLS} ${FROM}
    where s.state = 'published' and (s.search @@ websearch_to_tsquery('portuguese', $1) or s.title ilike '%' || $1 || '%')
    order by ts_rank(s.search, websearch_to_tsquery('portuguese', $1)) desc, s.published_at desc limit 30`, [q.trim().slice(0, 200)]));
}

export async function page(ctx: Ctx, slug: string) {
  const [p] = await withCtx(ctx, (tx) => tx<{ title: string; body: string; updated_at: Date }[]>`
    select title, body, updated_at from pages where slug = ${slug} and published`);
  return p ?? null;
}

export async function publishedPages(ctx: Ctx) {
  return withCtx(ctx, (tx) => tx<{ slug: string; title: string; updated_at: Date }[]>`select slug, title, updated_at from pages where published order by title`);
}
