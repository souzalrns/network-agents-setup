"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { login, logout } from "@/lib/auth-core";
import { requireLead, requireUser, SESSION_COOKIE } from "@/lib/auth";
import { isDesk, isLead, ROLES, type Role } from "@/lib/context";
import { dbMessage, withCtx } from "@/lib/db";
import { int, isDate, isHttpUrl, isUuid, lines, opt, str } from "@/lib/forms";
import { fromLocalInput } from "@/lib/format";
import { hashPassword } from "@/lib/password";
import { ConflictError, discardDraft, parseArticle, rescueDraft, restoreVersion, saveVersion } from "@/lib/drafts";
import { createStory, EditorialError, getStory, transition, updateStory } from "@/lib/stories";
import { slugify } from "@/lib/text";
import { isState, STATE_LABEL, type State } from "@/lib/workflow";

/** Volta à página com uma mensagem (erro ou confirmação), sem depender de JavaScript no browser. */
function back(path: string, kind: "erro" | "ok", msg: string): never {
  // a mensagem vai na query, antes do fragmento (#secção), senão o browser não a envia ao servidor
  const [base, hash] = path.split("#") as [string, string | undefined];
  const sep = base.includes("?") ? "&" : "?";
  redirect(`${base}${sep}${kind}=${encodeURIComponent(msg)}${hash ? `#${hash}` : ""}`);
}

function failMessage(e: unknown): string {
  if (e instanceof EditorialError) return e.message;
  const m = dbMessage(e);
  if (m) return m;
  console.error("[redacao]", e);
  return "Não foi possível guardar. Tenta outra vez.";
}

/** Corre a alteração; erros conhecidos voltam à página como mensagem. */
async function attempt(path: string, fn: () => Promise<unknown>): Promise<void> {
  try {
    await fn();
  } catch (e) {
    if ((e as { digest?: string })?.digest?.startsWith("NEXT_REDIRECT")) throw e;
    back(path, "erro", failMessage(e));
  }
}

const safePath = (p: string, dflt: string) => (p.startsWith("/redacao") && !p.startsWith("//") ? p : dflt);

// ------------------------------------------------------------------ sessão

export async function loginAction(form: FormData) {
  const email = str(form, "email", 200), password = str(form, "password", 500);
  if (!email || !password) back("/redacao/entrar", "erro", "Indica o email e a palavra-passe.");
  const r = await login(email, password, opt(form, "publicacao", 100) ?? undefined);
  if (!r.ok) back("/redacao/entrar", "erro", r.reason === "no_access" ? "Esta conta não tem acesso a nenhuma publicação." : "Email ou palavra-passe errados.");
  (await cookies()).set(SESSION_COOKIE, r.token, {
    httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "lax", path: "/", expires: r.expires,
  });
  redirect("/redacao");
}

export async function logoutAction() {
  const jar = await cookies();
  await logout(jar.get(SESSION_COOKIE)?.value);
  jar.delete(SESSION_COOKIE);
  redirect("/redacao/entrar");
}

// ------------------------------------------------------------------ pautas e peças

export async function createStoryAction(form: FormData) {
  const { ctx } = await requireUser();
  let id = "";
  await attempt("/redacao/pautas/nova", async () => {
    const section = opt(form, "section_id", 40);
    const due = str(form, "due_date", 10);
    const s = await createStory(ctx, {
      title: str(form, "title", 300), angle: str(form, "angle", 4000), toConfirm: str(form, "to_confirm", 4000),
      sectionId: section && isUuid(section) ? section : null, format: str(form, "format", 40) || "reportagem",
      priority: int(form, "priority", 1, 3, 2), interviewQuestions: lines(form, "interview_questions"),
      dueDate: isDate(due) ? due : null, propose: form.get("propose") === "1",
    });
    id = s.id;
  });
  revalidatePath("/redacao");
  redirect(`/redacao/pecas/${id}?ok=${encodeURIComponent("Pauta criada.")}`);
}

export async function updatePitchAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40);
  if (!isUuid(id)) back("/redacao/pautas", "erro", "Peça inválida.");
  const path = `/redacao/pecas/${id}`;
  await attempt(path, async () => {
    const section = opt(form, "section_id", 40);
    const assignee = opt(form, "assignee_id", 40);
    const due = str(form, "due_date", 10);
    await updateStory(ctx, id, {
      title: str(form, "title", 300), angle: str(form, "angle", 4000), to_confirm: str(form, "to_confirm", 4000),
      interview_questions: lines(form, "interview_questions"), format: str(form, "format", 40) || "reportagem",
      priority: int(form, "priority", 1, 3, 2), section_id: section && isUuid(section) ? section : null,
      due_date: isDate(due) ? due : null,
      ...(isDesk(ctx.role) ? { assignee_id: assignee && isUuid(assignee) ? assignee : null } : {}),
    }, str(form, "note", 300)); // numa peça publicada, mudar título ou editoria exige nota (regra da base de dados)
  });
  revalidatePath(path);
  back(`${path}#pauta`, "ok", "Pauta guardada.");
}

/**
 * «Guardar versão»: grava o artigo se a peça ainda estiver na versão em que o texto foi começado (base_version).
 * Se outra pessoa guardou entretanto, recusa e deixa o texto no rascunho do servidor: nada se perde.
 */
export async function updateArticleAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40);
  if (!isUuid(id)) back("/redacao/pautas", "erro", "Peça inválida.");
  const path = `/redacao/pecas/${id}`;
  // sem a versão de base não se sabe se alguém guardou entretanto: recusa em vez de gravar por cima
  const base = int(form, "base_version", 1, 1_000_000, 0);
  if (!base) back(`${path}#artigo`, "erro", "A página está desactualizada: recarrega-a antes de guardar (o teu texto continua no rascunho).");
  let fields: ReturnType<typeof parseArticle>;
  try { fields = parseArticle((k) => form.get(k)); } catch (e) { back(`${path}#artigo`, "erro", failMessage(e)); }
  if (!fields!.title) back(`${path}#artigo`, "erro", "A peça precisa de um título.");
  let msg = "Versão guardada.";
  let conflict = "";
  await attempt(`${path}#artigo`, async () => {
    try {
      const before = await withCtx(ctx, (tx) => getStory(tx, id));
      const saved = await saveVersion(ctx, id, fields!, base, str(form, "note", 300));
      if (before && saved.version === before.version) msg = "Não havia alterações para guardar.";
      else if (before && ["approved", "scheduled"].includes(before.state) && saved.state === "in_review") msg = "Versão guardada. A peça voltou a revisão: o texto aprovado era outro.";
    } catch (e) {
      if (!(e instanceof ConflictError)) throw e;
      // o texto desta pessoa fica guardado como rascunho, se o rascunho da peça for dela (ou não houver nenhum)
      const kept = await rescueDraft(ctx, id, base, fields!).catch(() => false);
      conflict = `${e.message} ${kept
        ? "O teu texto ficou guardado como rascunho: compara as versões e junta antes de guardar."
        : "Há um rascunho de outra pessoa nesta peça; o teu texto ficou na cópia deste browser: recupera-o no aviso do editor."}`;
    }
  });
  revalidatePath(path);
  if (conflict) back(`${path}#artigo`, "erro", conflict);
  back(`${path}#artigo`, "ok", msg);
}

export async function restoreVersionAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40);
  const path = `/redacao/pecas/${id}/versoes`;
  if (!isUuid(id)) back("/redacao/pautas", "erro", "Peça inválida.");
  const version = int(form, "version", 1, 1_000_000, 0), current = int(form, "current", 1, 1_000_000, 0);
  let made = 0;
  await attempt(path, async () => { made = (await restoreVersion(ctx, id, version, current)).version; });
  revalidatePath(`/redacao/pecas/${id}`);
  back(`/redacao/pecas/${id}#artigo`, "ok", `Versão ${version} restaurada como versão ${made}. O histórico ficou intacto.`);
}

export async function discardDraftAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40);
  if (!isUuid(id)) back("/redacao/pautas", "erro", "Peça inválida.");
  await attempt(`/redacao/pecas/${id}`, () => discardDraft(ctx, id));
  revalidatePath(`/redacao/pecas/${id}`);
  back(`/redacao/pecas/${id}#artigo`, "ok", "Rascunho descartado.");
}

export async function transitionAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), to = str(form, "to", 30);
  // o quadro de pautas volta ao quadro; a página da peça volta à peça
  const path = safePath(str(form, "back", 300), `/redacao/pecas/${id}`);
  if (!isUuid(id) || !isState(to)) back("/redacao/pautas", "erro", "Pedido inválido.");
  await attempt(path, async () => {
    const when = to === "scheduled" ? fromLocalInput(str(form, "scheduled_at", 20)) : null;
    await transition(ctx, id, to, { note: str(form, "note", 500), scheduledAt: when ?? undefined });
  });
  revalidatePath(`/redacao/pecas/${id}`);
  revalidatePath("/", "layout");
  back(path, "ok", path.startsWith("/redacao/pautas") ? `«${str(form, "title", 120) || "Peça"}» passou a ${STATE_LABEL[to as State]}.` : "Estado actualizado.");
}

export async function commentAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), body = str(form, "body", 5000);
  const path = `/redacao/pecas/${id}`;
  if (!isUuid(id)) back("/redacao/pautas", "erro", "Peça inválida.");
  if (!body) back(`${path}#comentarios`, "erro", "Escreve o comentário.");
  await attempt(path, () => withCtx(ctx, (tx) => tx`insert into comments (publication_id, story_id, author_id, author_label, body, kind)
    values (${ctx.publicationId}, ${id}, ${ctx.userId!}, ${ctx.label ?? ""}, ${body}, ${form.get("review") === "1" ? "review" : "comment"})`));
  revalidatePath(path);
  back(`${path}#comentarios`, "ok", "Comentário publicado.");
}

export async function resolveCommentAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), comment = str(form, "comment", 40);
  if (!isUuid(id) || !isUuid(comment)) back("/redacao/pautas", "erro", "Pedido inválido.");
  await attempt(`/redacao/pecas/${id}`, () => withCtx(ctx, (tx) => tx`update comments set resolved_at = now() where id = ${comment}`));
  revalidatePath(`/redacao/pecas/${id}`);
  back(`/redacao/pecas/${id}#comentarios`, "ok", "Comentário resolvido.");
}

// ------------------------------------------------------------------ afirmações, referências, fontes

const CLAIM_KINDS = ["fact", "statement", "inference", "unconfirmed"];
const VERIFICATIONS = ["pending", "verified", "disputed", "unsupported"];

export async function addClaimAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40);
  const path = `/redacao/pecas/${id}`;
  const kind = str(form, "kind", 20), text = str(form, "text", 2000);
  if (!isUuid(id) || !CLAIM_KINDS.includes(kind) || !text) back(`${path}#verificacao`, "erro", "Indica a afirmação e o tipo.");
  const url = str(form, "evidence_url", 1000);
  if (url && !isHttpUrl(url)) back(`${path}#verificacao`, "erro", "A evidência tem de ser um endereço http(s).");
  await attempt(path, () => withCtx(ctx, (tx) => tx`insert into claims (publication_id, story_id, text, kind, attributed_to, evidence, origin)
    values (${ctx.publicationId}, ${id}, ${text}, ${kind}, ${str(form, "attributed_to", 300)},
      ${tx.json(url ? [{ url, title: str(form, "evidence_title", 300), accessed_at: new Date().toISOString() }] : [])}, 'human')`));
  revalidatePath(path);
  back(`${path}#verificacao`, "ok", "Afirmação registada.");
}

/** Muda o que a afirmação diz no artigo (incluída ou não) e acrescenta evidência. Não verifica: isso é outra acção. */
export async function updateClaimAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), claim = str(form, "claim", 40);
  const path = `/redacao/pecas/${id}`;
  if (!isUuid(id) || !isUuid(claim)) back(`${path}#verificacao`, "erro", "Pedido inválido.");
  const url = str(form, "evidence_url", 1000);
  if (url && !isHttpUrl(url)) back(`${path}#verificacao`, "erro", "A evidência tem de ser um endereço http(s).");
  let reset = false;
  await attempt(path, () => withCtx(ctx, async (tx) => {
    const [before] = await tx<{ verification: string }[]>`select verification from claims where id = ${claim}`;
    const rows = url
      ? await tx<{ verification: string }[]>`update claims set in_article = ${form.get("in_article") === "1"},
          evidence = evidence || ${tx.json([{ url, title: str(form, "evidence_title", 300), accessed_at: new Date().toISOString() }])}
          where id = ${claim} returning verification`
      : await tx<{ verification: string }[]>`update claims set in_article = ${form.get("in_article") === "1"} where id = ${claim} returning verification`;
    if (!rows.length) throw new EditorialError("Não tens permissão para alterar esta afirmação.");
    reset = before?.verification === "verified" && rows[0]!.verification !== "verified";
  }));
  revalidatePath(path);
  back(`${path}#verificacao`, "ok", reset ? "Guardado. A evidência mudou, por isso a afirmação voltou a «por verificar»." : "Afirmação actualizada.");
}

/** Verificação: acção própria, feita por quem não escreveu a peça nem registou a afirmação (quatro olhos). */
export async function verifyClaimAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), claim = str(form, "claim", 40), verification = str(form, "verification", 20);
  const path = `/redacao/pecas/${id}`;
  if (!isUuid(id) || !isUuid(claim) || !VERIFICATIONS.includes(verification)) back(`${path}#verificacao`, "erro", "Pedido inválido.");
  await attempt(path, () => withCtx(ctx, async (tx) => {
    const rows = await tx`update claims set verification = ${verification} where id = ${claim} returning id`;
    if (!rows.length) throw new EditorialError("Não tens permissão para verificar esta afirmação.");
  }));
  revalidatePath(path);
  back(`${path}#verificacao`, "ok", "Verificação registada.");
}

export async function addRefAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), url = str(form, "url", 1000), kind = str(form, "kind", 20);
  const path = `/redacao/pecas/${id}`;
  if (!isUuid(id) || !isHttpUrl(url)) back(`${path}#referencias`, "erro", "Indica um endereço http(s) válido.");
  await attempt(path, () => withCtx(ctx, (tx) => tx`insert into story_refs (publication_id, story_id, kind, url, title, credit, note, added_by, added_kind)
    values (${ctx.publicationId}, ${id}, ${["document", "data", "article", "photo", "video", "audio"].includes(kind) ? kind : "document"},
      ${url}, ${str(form, "title", 300)}, ${str(form, "credit", 200)}, ${str(form, "note", 1000)}, ${ctx.userId!}, 'human')`));
  revalidatePath(path);
  back(`${path}#referencias`, "ok", "Referência acrescentada.");
}

export async function removeRefAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), ref = str(form, "ref", 40);
  if (!isUuid(id) || !isUuid(ref)) back("/redacao/pautas", "erro", "Pedido inválido.");
  await attempt(`/redacao/pecas/${id}`, () => withCtx(ctx, (tx) => tx`delete from story_refs where id = ${ref}`));
  revalidatePath(`/redacao/pecas/${id}`);
  back(`/redacao/pecas/${id}#referencias`, "ok", "Referência retirada.");
}

export async function saveSourceAction(form: FormData) {
  const { ctx } = await requireUser();
  const back_to = safePath(str(form, "back", 200), "/redacao/fontes");
  const name = str(form, "name", 200);
  if (!name) back(back_to, "erro", "A fonte precisa de um nome.");
  const conf = str(form, "confidentiality", 20), kind = str(form, "kind", 20);
  const sourceId = str(form, "source", 40);
  let createdId = "";
  await attempt(back_to, () => withCtx(ctx, async (tx) => {
    const values = { name, organization: str(form, "organization", 200), contact: str(form, "contact", 500), notes: str(form, "notes", 4000),
      kind: ["person", "institution", "document"].includes(kind) ? kind : "person",
      confidentiality: ["public", "internal", "protected"].includes(conf) ? conf : "internal" };
    if (isUuid(sourceId)) {
      const rows = await tx`update sources set ${tx(values)} where id = ${sourceId} returning id`;
      if (!rows.length) throw new EditorialError("Só quem registou a fonte (ou a direção) a pode alterar.");
      createdId = sourceId;
    } else {
      const [row] = await tx<{ id: string }[]>`insert into sources ${tx({ ...values, publication_id: ctx.publicationId, owner_id: ctx.userId! })} returning id`;
      createdId = row!.id;
    }
    const story = str(form, "story", 40);
    if (isUuid(story)) {
      const usage = str(form, "usage", 20);
      await tx`insert into story_sources (publication_id, story_id, source_id, usage)
        values (${ctx.publicationId}, ${story}, ${createdId}, ${["on_record", "background", "off_record"].includes(usage) ? usage : "on_record"})
        on conflict (story_id, source_id) do update set usage = excluded.usage`;
    }
  }));
  revalidatePath(back_to.split("?")[0]!.split("#")[0]!);
  back(back_to, "ok", "Fonte guardada.");
}

export async function linkSourceAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), source = str(form, "source", 40), usage = str(form, "usage", 20);
  const path = `/redacao/pecas/${id}`;
  if (!isUuid(id) || !isUuid(source)) back(`${path}#fontes`, "erro", "Escolhe uma fonte.");
  await attempt(path, () => withCtx(ctx, (tx) => tx`insert into story_sources (publication_id, story_id, source_id, usage)
    values (${ctx.publicationId}, ${id}, ${source}, ${["on_record", "background", "off_record"].includes(usage) ? usage : "on_record"})
    on conflict (story_id, source_id) do update set usage = excluded.usage`));
  revalidatePath(path);
  back(`${path}#fontes`, "ok", "Fonte associada.");
}

export async function unlinkSourceAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), source = str(form, "source", 40);
  if (!isUuid(id) || !isUuid(source)) back("/redacao/pautas", "erro", "Pedido inválido.");
  await attempt(`/redacao/pecas/${id}`, () => withCtx(ctx, (tx) => tx`delete from story_sources where story_id = ${id} and source_id = ${source}`));
  revalidatePath(`/redacao/pecas/${id}`);
  back(`/redacao/pecas/${id}#fontes`, "ok", "Fonte retirada da peça.");
}

export async function addCorrectionAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), text = str(form, "text", 2000);
  const path = `/redacao/pecas/${id}`;
  if (!isUuid(id) || !text) back(`${path}#correcoes`, "erro", "Escreve a nota de correção.");
  await attempt(path, () => withCtx(ctx, (tx) => tx`insert into corrections (publication_id, story_id, text, created_by)
    values (${ctx.publicationId}, ${id}, ${text}, ${ctx.userId!})`));
  revalidatePath(path);
  revalidatePath("/", "layout");
  back(`${path}#correcoes`, "ok", "Correção publicada no artigo.");
}

// ------------------------------------------------------------------ propostas dos agentes

export async function reviewOutputAction(form: FormData) {
  const { ctx } = await requireUser();
  const output = str(form, "output", 40), status = str(form, "status", 20);
  const path = safePath(str(form, "back", 200), "/redacao");
  if (!isUuid(output) || !["accepted", "dismissed"].includes(status)) back(path, "erro", "Pedido inválido.");
  await attempt(path, () => withCtx(ctx, async (tx) => {
    const rows = await tx`update agent_outputs set status = ${status}, reviewed_by = ${ctx.userId!}, reviewed_at = now()
      where id = ${output} returning id`;
    if (!rows.length) throw new EditorialError("Não tens permissão para rever esta proposta.");
  }));
  revalidatePath(path.split("?")[0]!.split("#")[0]!);
  back(path, "ok", status === "accepted" ? "Proposta marcada como aproveitada." : "Proposta descartada.");
}

// ------------------------------------------------------------------ distribuição

export async function saveDistributionAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), item = str(form, "item", 40), channel = str(form, "channel", 20);
  const path = `/redacao/pecas/${id}`;
  if (!isUuid(id) || !["instagram", "youtube", "podcast", "newsletter", "other"].includes(channel)) back(`${path}#distribuicao`, "erro", "Escolhe o canal.");
  const content = { text: str(form, "text", 5000), link: str(form, "link", 1000), media_url: str(form, "media_url", 1000) };
  await attempt(path, () => withCtx(ctx, async (tx) => {
    if (isUuid(item)) await tx`update distribution_items set content = ${tx.json(content)}, channel = ${channel} where id = ${item}`;
    else await tx`insert into distribution_items (publication_id, story_id, channel, content, prepared_kind, prepared_label)
      values (${ctx.publicationId}, ${id}, ${channel}, ${tx.json(content)}, 'human', ${ctx.label ?? ""})`;
  }));
  revalidatePath(path);
  back(`${path}#distribuicao`, "ok", "Conteúdo de distribuição guardado.");
}

export async function distributionStateAction(form: FormData) {
  const { ctx } = await requireUser();
  const id = str(form, "id", 40), item = str(form, "item", 40), state = str(form, "state", 20);
  const path = safePath(str(form, "back", 200), `/redacao/pecas/${id}#distribuicao`);
  if (!isUuid(item) || !["in_review", "approved", "discarded", "draft"].includes(state)) back(path, "erro", "Pedido inválido.");
  await attempt(path, () => withCtx(ctx, async (tx) => {
    const rows = await tx`update distribution_items set state = ${state} where id = ${item} returning id`;
    if (!rows.length) throw new EditorialError("Não tens permissão para alterar este conteúdo.");
  }));
  revalidatePath(path.split("#")[0]!);
  back(path, "ok", state === "approved" ? "Aprovado. Já pode seguir para o agendador." : "Estado actualizado.");
}

// ------------------------------------------------------------------ equipa, editorias, configuração

export async function addMemberAction(form: FormData) {
  const { ctx } = await requireLead();
  const role = str(form, "role", 20) as Role;
  const email = str(form, "email", 200).toLowerCase(), name = str(form, "name", 200), password = str(form, "password", 200);
  if (!ROLES.includes(role) || !email.includes("@") || !name) back("/redacao/equipa", "erro", "Preenche nome, email e papel.");
  if (password.length < 10) back("/redacao/equipa", "erro", "A palavra-passe inicial precisa de pelo menos 10 caracteres.");
  const hash = await hashPassword(password);
  await attempt("/redacao/equipa", () => withCtx(ctx, (tx) =>
    tx`select editorial.staff_create_member(${email}, ${name}, ${hash}, ${role}, ${slugify(str(form, "author_slug", 80) || name)})`));
  revalidatePath("/redacao/equipa");
  back("/redacao/equipa", "ok", `${name} entrou na equipa. Envia-lhe a palavra-passe inicial por um canal seguro.`);
}

export async function updateMemberAction(form: FormData) {
  const { ctx } = await requireUser();
  const user = str(form, "user", 40);
  if (!isUuid(user)) back("/redacao/equipa", "erro", "Pedido inválido.");
  const self = user === ctx.userId;
  if (!self && !isLead(ctx.role)) back("/redacao/equipa", "erro", "Só a direção altera a ficha de outra pessoa.");
  const role = str(form, "role", 20) as Role;
  await attempt("/redacao/equipa", () => withCtx(ctx, async (tx) => {
    const values: Record<string, unknown> = { display_name: str(form, "name", 200), bio: str(form, "bio", 1500),
      public_profile: form.get("public_profile") === "1" };
    if (!self && ROLES.includes(role)) values.role = role;
    const rows = await tx`update memberships set ${tx(values)} where user_id = ${user} returning user_id`;
    if (!rows.length) throw new EditorialError("Não foi possível alterar esta pessoa.");
  }));
  revalidatePath("/redacao/equipa");
  back("/redacao/equipa", "ok", "Ficha actualizada.");
}

export async function removeMemberAction(form: FormData) {
  const { ctx } = await requireLead();
  const user = str(form, "user", 40);
  if (!isUuid(user) || user === ctx.userId) back("/redacao/equipa", "erro", "Não te podes retirar a ti próprio da equipa.");
  await attempt("/redacao/equipa", () => withCtx(ctx, async (tx) => {
    const rows = await tx`delete from memberships where user_id = ${user} returning user_id`;
    if (!rows.length) throw new EditorialError("Não foi possível retirar esta pessoa.");
  }));
  revalidatePath("/redacao/equipa");
  back("/redacao/equipa", "ok", "A pessoa deixou de ter acesso a esta publicação.");
}

export async function changePasswordAction(form: FormData) {
  const { ctx } = await requireUser();
  const pw = str(form, "password", 200);
  if (pw.length < 10 || pw !== str(form, "confirm", 200)) back("/redacao/conta", "erro", "As palavras-passe não coincidem ou têm menos de 10 caracteres.");
  const hash = await hashPassword(pw);
  await attempt("/redacao/conta", () => withCtx(ctx, (tx) => tx`select editorial.staff_set_password(${ctx.userId!}, ${hash})`));
  redirect("/redacao/entrar?ok=" + encodeURIComponent("Palavra-passe alterada. Entra outra vez."));
}

export async function saveSectionAction(form: FormData) {
  const { ctx } = await requireLead();
  const name = str(form, "name", 120);
  if (!name) back("/redacao/configuracao#editorias", "erro", "A editoria precisa de nome.");
  const color = str(form, "color", 7);
  const values = { name, slug: slugify(str(form, "slug", 80) || name), description: str(form, "description", 600),
    color: /^#[0-9a-fA-F]{6}$/.test(color) ? color : "#7A8480", position: int(form, "position", 0, 999, 0), active: form.get("active") !== "0" };
  const section = str(form, "section", 40);
  await attempt("/redacao/configuracao", () => withCtx(ctx, (tx) => isUuid(section)
    ? tx`update sections set ${tx(values)} where id = ${section}`
    : tx`insert into sections ${tx({ ...values, publication_id: ctx.publicationId })}`));
  revalidatePath("/", "layout");
  back("/redacao/configuracao#editorias", "ok", "Editoria guardada.");
}

export async function savePublicationAction(form: FormData) {
  const { ctx } = await requireLead();
  const color = (k: string, d: string) => (/^#[0-9a-fA-F]{6}$/.test(str(form, k, 7)) ? str(form, k, 7) : d);
  const url = (k: string) => { const v = str(form, k, 1000); return v && isHttpUrl(v) ? v : null; };
  const social: Record<string, string> = {};
  for (const k of ["instagram", "youtube", "podcast", "tiktok", "x", "facebook", "linkedin", "newsletter"]) {
    const v = str(form, `social_${k}`, 300);
    if (v && isHttpUrl(v)) social[k] = v;
  }
  const legal: Record<string, string> = {};
  for (const k of ["owner", "director", "registration", "nipc", "statute_url", "address"]) {
    const v = str(form, `legal_${k}`, 400);
    if (v) legal[k] = v;
  }
  const agentNames: Record<string, string> = {};
  for (const k of ["editorial.radar", "editorial.research", "editorial.factcheck", "editorial.editor"]) {
    const v = str(form, `agent_${k}`, 60);
    if (v) agentNames[k] = v;
  }
  await attempt("/redacao/configuracao", () => withCtx(ctx, async (tx) => {
    const [p] = await tx<{ settings: Record<string, unknown> }[]>`select settings from publications where id = ${ctx.publicationId}`;
    await tx`update publications set ${tx({
      name: str(form, "name", 120) || "Publicação", tagline: str(form, "tagline", 200), description: str(form, "description", 1000),
      logo_url: url("logo_url"), favicon_url: url("favicon_url"), primary_color: color("primary_color", "#16211C"),
      secondary_color: color("secondary_color", "#F0B429"), domain: str(form, "domain", 200).toLowerCase() || null,
      contact_email: str(form, "contact_email", 200) || null, contact_address: str(form, "contact_address", 400) || null,
      language: str(form, "language", 10) || "pt-PT", public_launch: form.get("public_launch") === "1", updated_at: new Date(),
    })}, social_links = ${tx.json(social)}, legal = ${tx.json(legal)}, agent_names = ${tx.json(agentNames)},
      settings = ${tx.json({ ...(p?.settings ?? {}), require_second_reviewer: form.get("require_second_reviewer") === "1" })}
      where id = ${ctx.publicationId}`;
    await tx`insert into audit_log (publication_id, actor_kind, actor_user_id, actor_label, action, entity)
      values (${ctx.publicationId}, 'human', ${ctx.userId!}, ${ctx.label ?? ""}, 'publication.update', 'publication')`;
  }));
  revalidatePath("/", "layout");
  back("/redacao/configuracao", "ok", "Configuração guardada.");
}

export async function savePageAction(form: FormData) {
  const { ctx } = await requireLead();
  const slug = slugify(str(form, "slug", 80)), title = str(form, "title", 200);
  if (!title) back("/redacao/configuracao#paginas", "erro", "A página precisa de título.");
  await attempt("/redacao/configuracao", () => withCtx(ctx, (tx) => tx`insert into pages (publication_id, slug, title, body, published, updated_by)
    values (${ctx.publicationId}, ${slug}, ${title}, ${str(form, "body", 100_000)}, ${form.get("published") === "1"}, ${ctx.userId!})
    on conflict (publication_id, slug) do update set title = excluded.title, body = excluded.body, published = excluded.published,
      updated_by = excluded.updated_by, updated_at = now()`));
  revalidatePath("/", "layout");
  back("/redacao/configuracao#paginas", "ok", "Página guardada.");
}
