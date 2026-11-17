import { type Ctx, canWrite } from "./context";
import { type Tx, withCtx } from "./db";
import { slugify } from "./text";
import { canTransition, isState, type State, STATE_LABEL } from "./workflow";

export interface Story {
  id: string; publication_id: string; section_id: string | null; state: State; priority: number; format: string;
  origin: "human" | "agent" | "radar"; title: string; angle: string; to_confirm: string; interview_questions: string[];
  due_date: string | null; assignee_id: string | null; created_by: string | null; slug: string | null; subtitle: string;
  summary: string; body: string; author_id: string | null; hero_image_url: string | null; hero_caption: string;
  hero_credit: string; tags: string[]; seo_title: string; meta_description: string; kind: string;
  scheduled_at: Date | null; approved_by: string | null; approved_at: Date | null; published_at: Date | null;
  version: number; created_at: Date; updated_at: Date; approved_version: number | null; approved_fingerprint: string | null;
}

export class EditorialError extends Error {}

const PITCH_FIELDS = ["title", "angle", "to_confirm", "interview_questions", "due_date", "priority", "format", "section_id", "assignee_id"] as const;
const ARTICLE_FIELDS = ["slug", "subtitle", "summary", "body", "author_id", "hero_image_url", "hero_caption", "hero_credit",
  "tags", "seo_title", "meta_description", "kind"] as const;
const EDITABLE = new Set<string>([...PITCH_FIELDS, ...ARTICLE_FIELDS]);
export type StoryPatch = Partial<Pick<Story, (typeof PITCH_FIELDS)[number] | (typeof ARTICLE_FIELDS)[number]>>;

const COLS = `id, publication_id, section_id, state, priority, format, origin, title, angle, to_confirm, interview_questions,
  due_date::text as due_date, assignee_id, created_by, slug, subtitle, summary, body, author_id, hero_image_url, hero_caption,
  hero_credit, tags, seo_title, meta_description, kind, scheduled_at, approved_by, approved_at, published_at, version,
  created_at, updated_at, approved_version, approved_fingerprint`;

export async function getStory(tx: Tx, id: string): Promise<Story | null> {
  const [row] = await tx.unsafe<Story[]>(`select ${COLS} from stories where id = $1`, [id]);
  return row ?? null;
}

export interface NewStory {
  title: string; angle?: string; toConfirm?: string; sectionId?: string | null; format?: string; priority?: number;
  interviewQuestions?: string[]; dueDate?: string | null; propose?: boolean;
}

/** Nova ideia (ou pauta já proposta). Pessoas criam com o seu nome; agentes e radar só criam ideias. */
export async function createStory(ctx: Ctx, input: NewStory): Promise<Story> {
  const title = input.title.trim();
  if (!title) throw new EditorialError("A pauta precisa de um título.");
  const origin = ctx.kind === "human" ? "human" : ctx.kind === "agent" ? "agent" : "radar";
  const state: State = ctx.kind === "human" && input.propose ? "pitch_proposed" : "idea";
  return withCtx(ctx, async (tx) => {
    const [row] = await tx.unsafe<Story[]>(
      `insert into stories (publication_id, section_id, state, priority, format, origin, title, angle, to_confirm,
         interview_questions, due_date, created_by)
       values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) returning ${COLS}`,
      [ctx.publicationId, input.sectionId ?? null, state, input.priority ?? 2, input.format ?? "reportagem", origin, title,
        input.angle ?? "", input.toConfirm ?? "", input.interviewQuestions ?? [], input.dueDate ?? null,
        ctx.kind === "human" ? ctx.userId ?? null : null]);
    return row!;
  });
}

/** Altera campos da pauta ou do artigo. A base de dados decide se este actor pode, e regista a versão. */
export async function updateStory(ctx: Ctx, id: string, patch: StoryPatch, note = "", expectedVersion?: number): Promise<Story> {
  const entries = Object.entries(patch).filter(([k, v]) => EDITABLE.has(k) && v !== undefined);
  if (!entries.length) throw new EditorialError("Nada para alterar.");
  if (patch.title !== undefined && !patch.title.trim()) throw new EditorialError("A peça precisa de um título.");
  if (patch.slug) patch.slug = slugify(patch.slug);
  return withCtx(ctx, async (tx) => {
    const sets = entries.map(([k], i) => `${k} = $${i + 2}`).join(", ");
    const values = entries.map(([k]) => (patch as Record<string, unknown>)[k] ?? null);
    // com expectedVersion, só grava se ninguém tiver gravado entretanto (a última gravação não ganha em silêncio)
    const guard = expectedVersion === undefined ? "" : ` and version = $${values.length + 2}`;
    const params = expectedVersion === undefined ? [id, ...values] : [id, ...values, expectedVersion];
    const [row] = await tx.unsafe<Story[]>(`update stories set ${sets} where id = $1${guard} returning ${COLS}`, params as never[]);
    if (!row && expectedVersion !== undefined) {
      const [cur] = await tx<{ version: number }[]>`select version from stories where id = ${id}`;
      if (cur && cur.version !== expectedVersion) {
        throw new EditorialError(`Outra pessoa guardou a versão ${cur.version} enquanto escrevias (começaste na ${expectedVersion}). Compara e junta antes de guardar.`);
      }
    }
    if (!row) throw new EditorialError("Não encontrei a peça ou não tens permissão para a alterar.");
    return row;
  }, note);
}

export interface TransitionOpts { note?: string; scheduledAt?: Date }

/**
 * Muda o estado de uma peça. Verifica a regra do fluxo para este papel (mensagem clara) e deixa a base de
 * dados impor o resto: quatro olhos, afirmações por verificar, agendamento, publicação só com aprovação humana.
 */
export async function transition(ctx: Ctx, id: string, to: State, opts: TransitionOpts = {}): Promise<Story> {
  if (!isState(to)) throw new EditorialError("Estado desconhecido.");
  return withCtx(ctx, async (tx) => {
    const story = await getStory(tx, id);
    if (!story) throw new EditorialError("Não encontrei a peça.");
    if (ctx.kind === "human") {
      if (!canWrite(ctx.role)) throw new EditorialError("O teu papel só permite ler e comentar.");
      const actors = { assigneeId: story.assignee_id, authorId: story.author_id, createdBy: story.created_by };
      if (!canTransition(story.state, to, ctx.role, ctx.userId, actors)) {
        throw new EditorialError(`Não podes passar esta peça de «${STATE_LABEL[story.state]}» para «${STATE_LABEL[to]}».`);
      }
    }
    const extra: string[] = [];
    const values: unknown[] = [id, to];
    if (to === "scheduled") {
      if (!opts.scheduledAt) throw new EditorialError("Indica a data e a hora de publicação.");
      values.push(opts.scheduledAt); extra.push(`scheduled_at = $${values.length}`);
    }
    if (to === "pitch_proposed" && !story.created_by && ctx.kind === "human") {
      values.push(ctx.userId ?? null);
      extra.push(`created_by = $${values.length}`); // adopta a ideia do agente ou do radar
    }
    // ao entrar em redacção, a peça ganha endereço e autor se ainda não os tem
    if (to === "writing" || to === "in_review") {
      if (!story.slug) { values.push(await freeSlug(tx, story.title)); extra.push(`slug = $${values.length}`); }
      if (!story.author_id) { values.push(story.assignee_id ?? ctx.userId ?? null); extra.push(`author_id = $${values.length}`); }
    }
    const [row] = await tx.unsafe<Story[]>(
      `update stories set state = $2${extra.length ? `, ${extra.join(", ")}` : ""} where id = $1 returning ${COLS}`, values as never[]);
    if (!row) throw new EditorialError("Não tens permissão para alterar esta peça.");
    return row;
  }, opts.note ?? "");
}

async function freeSlug(tx: Tx, title: string): Promise<string> {
  const base = slugify(title);
  for (let i = 0; i < 50; i++) {
    const candidate = i === 0 ? base : `${base}-${i + 1}`;
    const [hit] = await tx`select 1 from stories where slug = ${candidate} limit 1`;
    if (!hit) return candidate;
  }
  return `${base}-${Date.now()}`;
}

/**
 * Publica as peças agendadas cuja hora chegou. Corre como `system`: só executa o que uma pessoa agendou.
 * Cada peça é tentada à parte (ponto de gravação): se uma for recusada pela base de dados (conteúdo que já
 * não é o aprovado, afirmação por verificar), fica agendada e as outras publicam-se na mesma.
 */
export async function publishDue(ctx: Ctx): Promise<string[]> {
  if (ctx.kind !== "system") throw new EditorialError("A publicação agendada é uma tarefa do sistema.");
  return withCtx(ctx, async (tx) => {
    const due = await tx<{ id: string }[]>`select id from stories where state = 'scheduled' and scheduled_at <= now() order by scheduled_at`;
    const done: string[] = [];
    for (const { id } of due) {
      try {
        await tx.savepoint(async (sp) => { await sp`update stories set state = 'published' where id = ${id}`; });
        done.push(id);
      } catch (e) {
        console.warn("[publicação agendada] recusada", id, (e as Error).message);
      }
    }
    return done;
  }, "publicação agendada");
}
