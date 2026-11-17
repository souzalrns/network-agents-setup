import type { Ctx, Role } from "./context";
import { type Tx, withCtx } from "./db";
import type { Story } from "./stories";
import type { State } from "./workflow";

export interface StoryRow {
  id: string; title: string; state: State; priority: number; format: string; origin: string;
  section_id: string | null; section_name: string | null; section_color: string | null;
  assignee_id: string | null; assignee_name: string | null; author_name: string | null;
  due_date: string | null; scheduled_at: Date | null; published_at: Date | null; updated_at: Date; slug: string | null;
}

const ROW = `s.id, s.title, s.state, s.priority, s.format, s.origin, s.section_id, sec.name as section_name, sec.color as section_color,
  s.assignee_id, ma.display_name as assignee_name, mu.display_name as author_name, s.due_date::text as due_date,
  s.scheduled_at, s.published_at, s.updated_at, s.slug`;
const FROM = `from stories s
  left join sections sec on sec.id = s.section_id
  left join memberships ma on ma.user_id = s.assignee_id and ma.publication_id = s.publication_id
  left join memberships mu on mu.user_id = s.author_id and mu.publication_id = s.publication_id`;

export interface StoryFilter { state?: State | "active" | ""; section?: string; q?: string; mine?: string; limit?: number }

export async function listStories(ctx: Ctx, f: StoryFilter = {}): Promise<StoryRow[]> {
  return withCtx(ctx, (tx) => listStoriesTx(tx, f));
}

export async function listStoriesTx(tx: Tx, f: StoryFilter = {}): Promise<StoryRow[]> {
  const where: string[] = [];
  const v: unknown[] = [];
  if (f.state === "active") where.push(`s.state not in ('published', 'archived')`);
  else if (f.state) { v.push(f.state); where.push(`s.state = $${v.length}`); }
  if (f.section) { v.push(f.section); where.push(`s.section_id = $${v.length}`); }
  if (f.mine) { v.push(f.mine); where.push(`(s.assignee_id = $${v.length} or s.author_id = $${v.length})`); }
  if (f.q?.trim()) {
    v.push(f.q.trim());
    where.push(`(s.search @@ websearch_to_tsquery('portuguese', $${v.length}) or s.title ilike '%' || $${v.length} || '%')`);
  }
  v.push(Math.min(f.limit ?? 200, 500));
  return tx.unsafe<StoryRow[]>(
    `select ${ROW} ${FROM} ${where.length ? `where ${where.join(" and ")}` : ""}
     order by s.priority, coalesce(s.due_date, '9999-12-31'), s.updated_at desc limit $${v.length}`, v as never[]);
}

export interface Member { user_id: string; name: string; email: string; role: Role; author_slug: string; bio: string; public_profile: boolean }

export async function listTeam(tx: Tx): Promise<Member[]> {
  return tx<Member[]>`select m.user_id, m.display_name as name, u.email, m.role, m.author_slug, m.bio, m.public_profile
    from memberships m join users u on u.id = m.user_id order by m.role, m.display_name`;
}

export interface Section { id: string; slug: string; name: string; description: string; color: string; position: number; active: boolean }
export async function listSections(tx: Tx, activeOnly = false): Promise<Section[]> {
  return activeOnly
    ? tx<Section[]>`select * from sections where active order by position, name`
    : tx<Section[]>`select * from sections order by position, name`;
}

export interface Dashboard {
  counts: Record<State, number>;
  mine: StoryRow[]; review: StoryRow[]; pitches: StoryRow[]; scheduled: StoryRow[]; recent: StoryRow[];
  overdue: StoryRow[]; suggestions: number; radarNew: number;
  activity: { at: Date; actor_label: string; actor_kind: string; type: string; to_state: State | null; story_id: string; title: string }[];
  publishedWeek: number;
}

export async function dashboard(ctx: Ctx): Promise<Dashboard> {
  return withCtx(ctx, async (tx) => {
    const counts = Object.fromEntries((await tx<{ state: State; n: number }[]>`
      select state, count(*)::int as n from stories group by state`).map((r) => [r.state, r.n])) as Record<State, number>;
    const mine = ctx.userId ? await listStoriesTx(tx, { mine: ctx.userId, state: "active", limit: 12 }) : [];
    const review = await listStoriesTx(tx, { state: "in_review", limit: 12 });
    const pitches = await listStoriesTx(tx, { state: "pitch_proposed", limit: 12 });
    const scheduled = await tx.unsafe<StoryRow[]>(`select ${ROW} ${FROM} where s.state = 'scheduled' order by s.scheduled_at limit 10`);
    const recent = await tx.unsafe<StoryRow[]>(`select ${ROW} ${FROM} where s.state = 'published' order by s.published_at desc limit 6`);
    const overdue = await tx.unsafe<StoryRow[]>(`select ${ROW} ${FROM}
      where s.due_date < current_date and s.state not in ('published','archived','scheduled') order by s.due_date limit 10`);
    const [{ n: suggestions } = { n: 0 }] = await tx<{ n: number }[]>`select count(*)::int as n from agent_outputs where status = 'proposed'`;
    const [{ n: radarNew } = { n: 0 }] = await tx<{ n: number }[]>`select count(*)::int as n from feed_items where status = 'new' and duplicate_of is null`;
    const [{ n: publishedWeek } = { n: 0 }] = await tx<{ n: number }[]>`
      select count(*)::int as n from stories where state = 'published' and published_at > now() - interval '7 days'`;
    const activity = await tx<Dashboard["activity"]>`
      select e.at, e.actor_label, e.actor_kind, e.type, e.to_state, e.story_id, s.title
      from story_events e join stories s on s.id = e.story_id order by e.id desc limit 15`;
    return { counts, mine, review, pitches, scheduled, recent, overdue, suggestions, radarNew, activity, publishedWeek };
  });
}

export interface StoryDetail {
  story: Story;
  events: { id: number; type: string; from_state: State | null; to_state: State | null; actor_kind: string; actor_label: string; note: string; at: Date }[];
  versions: { version: number; saved_kind: string; saved_at: Date; name: string | null; words: number }[];
  comments: { id: string; author_label: string; author_kind: string; name: string | null; body: string; kind: string; created_at: Date; resolved_at: Date | null }[];
  claims: { id: string; text: string; kind: string; attributed_to: string; evidence: { url: string; title?: string }[]; verification: string; in_article: boolean; origin: string; verified_name: string | null }[];
  refs: { id: string; kind: string; url: string; title: string; credit: string; note: string; added_kind: string }[];
  sources: { id: string; name: string; organization: string; usage: string; confidentiality: string; contact: string }[];
  outputs: { id: string; agent_id: string; kind: string; payload: Record<string, unknown>; status: string; created_at: Date }[];
  distribution: { id: string; channel: string; kind: string; content: Record<string, unknown>; state: string; prepared_label: string; approved_at: Date | null }[];
  corrections: { id: string; text: string; created_at: Date }[];
}

export async function storyDetail(ctx: Ctx, id: string): Promise<StoryDetail | null> {
  return withCtx(ctx, async (tx) => {
    const { getStory } = await import("./stories");
    const story = await getStory(tx, id);
    if (!story) return null;
    const events = await tx<StoryDetail["events"]>`select id, type, from_state, to_state, actor_kind, actor_label, note, at
      from story_events where story_id = ${id} order by id desc limit 100`;
    const versions = await tx<StoryDetail["versions"]>`select v.version, v.saved_kind, v.saved_at, m.display_name as name,
      coalesce(array_length(regexp_split_to_array(btrim(v.body), '\\s+'), 1), 0) as words
      from story_versions v left join memberships m on m.user_id = v.saved_by and m.publication_id = v.publication_id
      where v.story_id = ${id} order by v.version desc limit 50`;
    const comments = await tx<StoryDetail["comments"]>`select c.id, c.author_label, c.author_kind, m.display_name as name, c.body, c.kind,
      c.created_at, c.resolved_at from comments c left join memberships m on m.user_id = c.author_id and m.publication_id = c.publication_id
      where c.story_id = ${id} order by c.created_at`;
    const claims = await tx<StoryDetail["claims"]>`select c.id, c.text, c.kind, c.attributed_to, c.evidence, c.verification, c.in_article,
      c.origin, m.display_name as verified_name from claims c
      left join memberships m on m.user_id = c.verified_by and m.publication_id = c.publication_id
      where c.story_id = ${id} order by c.created_at`;
    const refs = await tx<StoryDetail["refs"]>`select id, kind, url, title, credit, note, added_kind from story_refs where story_id = ${id} order by created_at`;
    const sources = await tx<StoryDetail["sources"]>`select s.id, s.name, s.organization, ss.usage, s.confidentiality, s.contact
      from story_sources ss join sources s on s.id = ss.source_id where ss.story_id = ${id} order by s.name`;
    const outputs = await tx<StoryDetail["outputs"]>`select id, agent_id, kind, payload, status, created_at from agent_outputs
      where story_id = ${id} order by created_at desc limit 20`;
    const distribution = await tx<StoryDetail["distribution"]>`select id, channel, kind, content, state, prepared_label, approved_at
      from distribution_items where story_id = ${id} order by created_at`;
    const corrections = await tx<StoryDetail["corrections"]>`select id, text, created_at from corrections where story_id = ${id} order by created_at`;
    return { story, events, versions, comments, claims, refs, sources, outputs, distribution, corrections };
  });
}

export interface SourceRow { id: string; name: string; organization: string; kind: string; contact: string; notes: string; confidentiality: string; owner_name: string | null; stories: number }
export async function listSources(ctx: Ctx, q = ""): Promise<SourceRow[]> {
  return withCtx(ctx, (tx) => tx<SourceRow[]>`
    select s.id, s.name, s.organization, s.kind, s.contact, s.notes, s.confidentiality, m.display_name as owner_name,
      (select count(*)::int from story_sources ss where ss.source_id = s.id) as stories
    from sources s left join memberships m on m.user_id = s.owner_id and m.publication_id = s.publication_id
    where ${q} = '' or s.name ilike '%' || ${q} || '%' or s.organization ilike '%' || ${q} || '%'
    order by s.name limit 300`);
}
