import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { agentCtx, systemCtx } from "@/lib/context";
import { closeDb, withCtx } from "@/lib/db";
import { createStory, EditorialError, getStory, publishDue, transition, updateStory } from "@/lib/stories";
import { canTransition, nextSteps, STATES } from "@/lib/workflow";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

let N: Newsroom;
beforeAll(async () => { N = await newsroom(); });
afterAll(async () => { await closeDb(); await closeOwner(); });

/** Leva uma peça nova até «em revisão», escrita pelo jornalista. */
async function emRevisao(title = "Peça em revisão") {
  const j = N.as("journalist");
  const s = await createStory(j, { title, sectionId: N.sectionId, propose: true });
  await transition(N.as("editor"), s.id, "pitch_approved");
  await updateStory(N.as("editor"), s.id, { assignee_id: N.users.journalist!.id });
  await transition(j, s.id, "researching");
  await transition(j, s.id, "interviewing");
  await transition(j, s.id, "writing");
  await updateStory(j, s.id, { body: "Texto da reportagem.", summary: "Resumo." });
  return transition(j, s.id, "in_review");
}

const eventos = (id: string) => ownerDb()<{ type: string; from_state: string | null; to_state: string | null; actor_kind: string; actor_user_id: string | null }[]>`
  select type, from_state, to_state, actor_kind, actor_user_id from story_events where story_id = ${id} order by id`;

describe("fluxo editorial de ponta a ponta", () => {
  it("percorre os 11 estados, com cada mudança registada e atribuída a quem a fez", async () => {
    const s = await emRevisao("Do princípio ao fim");
    expect(s.state).toBe("in_review");
    expect(s.slug).toBe("do-principio-ao-fim");
    expect(s.author_id).toBe(N.users.journalist!.id);
    await transition(N.as("editor"), s.id, "approved");
    const quando = new Date(Date.now() + 3_600_000);
    const agendada = await transition(N.as("director"), s.id, "scheduled", { scheduledAt: quando });
    expect(agendada.state).toBe("scheduled");
    const publicada = await transition(N.as("director"), s.id, "published");
    expect(publicada.published_at).toBeInstanceOf(Date);
    const arquivada = await transition(N.as("director"), s.id, "archived");
    expect(arquivada.state).toBe("archived");

    const ev = (await eventos(s.id)).filter((e) => e.type === "state_change");
    expect(ev.map((e) => e.to_state)).toEqual(["pitch_proposed", "pitch_approved", "researching", "interviewing",
      "writing", "in_review", "approved", "scheduled", "published", "archived"]);
    expect(ev.every((e) => e.actor_kind === "human" && e.actor_user_id)).toBe(true);
    expect(ev[1]!.actor_user_id).toBe(N.users.editor!.id);
    expect(new Set(STATES)).toEqual(new Set(["idea", ...ev.map((e) => e.to_state!)]));
  });

  it("guarda uma versão por cada alteração de texto, com quem a gravou", async () => {
    const j = N.as("journalist");
    const s = await createStory(j, { title: "Versões" });
    await updateStory(j, s.id, { body: "primeira" });
    await updateStory(j, s.id, { body: "segunda", title: "Versões (revisto)" });
    await updateStory(j, s.id, { priority: 1 }); // não é texto: não cria versão
    const v = await ownerDb()`select version, body, title, saved_by from story_versions where story_id = ${s.id} order by version`;
    expect(v.map((r) => [r.version, r.body])).toEqual([[1, ""], [2, "primeira"], [3, "segunda"]]);
    expect(v[2]!.title).toBe("Versões (revisto)");
    expect(v.every((r) => r.saved_by === N.users.journalist!.id)).toBe(true);
  });
});

describe("quem pode o quê", () => {
  it("um jornalista não aprova pautas nem artigos, nem publica", async () => {
    const s = await createStory(N.as("journalist"), { title: "Sem atalhos", propose: true });
    await expect(transition(N.as("journalist"), s.id, "pitch_approved")).rejects.toBeInstanceOf(EditorialError);
    const r = await emRevisao("Sem atalhos 2");
    await expect(transition(N.as("journalist"), r.id, "approved")).rejects.toBeInstanceOf(EditorialError);
    // mesmo contornando a aplicação, a base de dados recusa
    await expect(withCtx(N.as("journalist"), (tx) => tx`update stories set state = 'approved' where id = ${r.id}`))
      .rejects.toThrow(/edição ou da direcção/);
    await expect(withCtx(N.as("journalist"), (tx) => tx`update stories set state = 'published' where id = ${r.id}`))
      .rejects.toThrow(/edição ou da direcção/);
  });

  it("um jornalista não mexe nas peças dos colegas", async () => {
    const s = await createStory(N.as("journalist"), { title: "É minha" });
    await expect(updateStory(N.as("journalist2"), s.id, { title: "Agora é minha" })).rejects.toBeInstanceOf(EditorialError);
    await expect(transition(N.as("journalist2"), s.id, "pitch_proposed")).rejects.toBeInstanceOf(EditorialError);
    expect(await getStoryAsOwner(s.id)).toMatchObject({ title: "É minha", state: "idea" });
    // uma ideia de um agente não tem dono: quem a propõe adopta-a
    const ideia = await createStory(agentCtx(N.publicationId, "editorial.radar"), { title: "Sugestão sem dono" });
    const adoptada = await transition(N.as("journalist2"), ideia.id, "pitch_proposed");
    expect(adoptada).toMatchObject({ state: "pitch_proposed", created_by: N.users.journalist2!.id, origin: "agent" });
    await expect(updateStory(N.as("journalist"), ideia.id, { title: "tomada" })).rejects.toBeInstanceOf(EditorialError);
  });

  it("quem só revê não cria nem altera peças, mas comenta", async () => {
    const s = await emRevisao("Para rever");
    await expect(createStory(N.as("reviewer"), { title: "do revisor" })).rejects.toMatchObject({ code: "42501" });
    await expect(updateStory(N.as("reviewer"), s.id, { body: "reescrito" })).rejects.toBeInstanceOf(EditorialError);
    await expect(transition(N.as("reviewer"), s.id, "approved")).rejects.toBeInstanceOf(EditorialError);
    await withCtx(N.as("reviewer"), (tx) => tx`insert into comments (publication_id, story_id, author_id, body, kind)
      values (${N.publicationId}, ${s.id}, ${N.users.reviewer!.id}, 'Falta ouvir a outra parte.', 'review')`);
    expect(nextSteps("in_review", "reviewer", N.users.reviewer!.id, {})).toEqual([]);
  });

  it("quem escreveu a peça não a aprova (quatro olhos), salvo se a publicação desligar a regra", async () => {
    const e = N.as("editor");
    const s = await createStory(e, { title: "Escrita pela edição", sectionId: N.sectionId, propose: true });
    await transition(e, s.id, "pitch_approved");
    await transition(e, s.id, "writing");
    await updateStory(e, s.id, { body: "Texto." });
    await transition(e, s.id, "in_review");
    await expect(transition(e, s.id, "approved")).rejects.toThrow(/quem escreveu a peça não a aprova/);
    await expect(transition(N.as("director"), s.id, "approved")).resolves.toMatchObject({ state: "approved", approved_by: N.users.director!.id });

    const solo = await newsroom({ require_second_reviewer: false });
    const d = solo.as("director");
    const t = await createStory(d, { title: "Redacção de uma pessoa", sectionId: solo.sectionId, propose: true });
    await transition(d, t.id, "pitch_approved");
    await transition(d, t.id, "writing");
    await updateStory(d, t.id, { body: "Texto." });
    await transition(d, t.id, "in_review");
    await expect(transition(d, t.id, "approved")).resolves.toMatchObject({ state: "approved" });
  });

  it("a matriz de transições não deixa saltar a aprovação", () => {
    for (const from of STATES) {
      if (from !== "approved" && from !== "scheduled" && from !== "archived") {
        expect(canTransition(from, "published", "admin", "u", {}), from).toBe(false);
      }
    }
    expect(canTransition("writing", "approved", "admin", "u", {})).toBe(false);
    expect(canTransition("idea", "pitch_approved", "director", "u", {})).toBe(false);
  });
});

describe("aprovação, agendamento e publicação", () => {
  it("não se aprova sem texto, editoria, autor e endereço", async () => {
    const j = N.as("journalist");
    const s = await createStory(j, { title: "Incompleta", propose: true });
    await transition(N.as("editor"), s.id, "pitch_approved");
    await transition(j, s.id, "writing");
    await transition(j, s.id, "in_review");
    await expect(transition(N.as("editor"), s.id, "approved")).rejects.toThrow(/falta texto, editoria, autor ou endereço/);
  });

  it("não se publica uma peça que não foi aprovada, nem por um administrador directamente na base de dados", async () => {
    const s = await emRevisao("Sem aprovação");
    await expect(withCtx(N.as("admin"), (tx) => tx`update stories set state = 'published' where id = ${s.id}`))
      .rejects.toThrow(/só se publica uma peça aprovada/);
    await expect(withCtx(N.as("admin"), (tx) => tx`update stories set state = 'scheduled', scheduled_at = now() + interval '1 hour' where id = ${s.id}`))
      .rejects.toThrow(/só se agenda uma peça aprovada/);
  });

  it("alterar o texto de uma peça aprovada retira a aprovação", async () => {
    const s = await emRevisao("Aprovada e depois mexida");
    await transition(N.as("editor"), s.id, "approved");
    const depois = await updateStory(N.as("director"), s.id, { body: "Texto alterado depois de aprovado." });
    expect(depois.state).toBe("in_review");
    expect(depois.approved_by).toBeNull();
    await expect(withCtx(N.as("director"), (tx) => tx`update stories set state = 'published' where id = ${s.id}`))
      .rejects.toThrow(/só se publica uma peça aprovada/);
    // um redactor não altera de todo uma peça aprovada
    await transition(N.as("editor"), s.id, "approved");
    await expect(updateStory(N.as("journalist"), s.id, { body: "mexida pelo autor" })).rejects.toThrow(/só é alterada pela edição/);
  });

  it("a data de agendamento tem de ser futura e cancelar o agendamento mantém a aprovação", async () => {
    const s = await emRevisao("Agendar");
    await transition(N.as("editor"), s.id, "approved");
    await expect(transition(N.as("editor"), s.id, "scheduled", { scheduledAt: new Date(Date.now() - 60_000) })).rejects.toThrow(/tem de ser futura/);
    await expect(transition(N.as("editor"), s.id, "scheduled")).rejects.toThrow(/Indica a data/);
    await transition(N.as("editor"), s.id, "scheduled", { scheduledAt: new Date(Date.now() + 86_400_000) });
    const cancelada = await transition(N.as("editor"), s.id, "approved");
    expect(cancelada).toMatchObject({ state: "approved", scheduled_at: null, approved_by: N.users.editor!.id });
  });

  it("o sistema publica só o que uma pessoa agendou, e só quando a hora chega", async () => {
    const sys = systemCtx(N.publicationId, "publicação agendada");
    const cedo = await emRevisao("Agendada para amanhã");
    await transition(N.as("editor"), cedo.id, "approved");
    await transition(N.as("editor"), cedo.id, "scheduled", { scheduledAt: new Date(Date.now() + 86_400_000) });
    const hora = await emRevisao("Agendada e na hora");
    await transition(N.as("editor"), hora.id, "approved");
    await transition(N.as("editor"), hora.id, "scheduled", { scheduledAt: new Date(Date.now() + 86_400_000) });
    await passouAHora(hora.id);
    const aprovada = await emRevisao("Aprovada mas não agendada");
    await transition(N.as("editor"), aprovada.id, "approved");

    expect(await publishDue(sys)).toEqual([hora.id]);
    expect((await getStoryAsOwner(cedo.id)).state).toBe("scheduled");
    expect((await getStoryAsOwner(aprovada.id)).state).toBe("approved");
    const ultimo = (await eventos(hora.id)).at(-1)!;
    expect(ultimo).toMatchObject({ to_state: "published", actor_kind: "system", actor_user_id: null });
    // o sistema não publica antes da hora nem mexe no texto ao publicar
    await expect(withCtx(sys, (tx) => tx`update stories set state = 'published' where id = ${cedo.id}`)).rejects.toThrow(/à hora marcada/);
    await passouAHora(cedo.id);
    await expect(withCtx(sys, (tx) => tx`update stories set state = 'published', body = 'texto trocado' where id = ${cedo.id}`)).rejects.toThrow(/à hora marcada/);
    await expect(publishDue(N.as("director"))).rejects.toBeInstanceOf(EditorialError);
  });

  it("um agente nunca aprova, agenda nem publica", async () => {
    const s = await emRevisao("Fora do alcance do agente");
    const agent = agentCtx(N.publicationId, "editorial.editor");
    await expect(transition(agent, s.id, "approved")).rejects.toBeInstanceOf(EditorialError);
    for (const st of ["approved", "published", "scheduled", "archived"]) {
      const rows = await withCtx(agent, (tx) => tx`update stories set state = ${st}::story_state where id = ${s.id} returning id`);
      expect(rows.length, st).toBe(0);
    }
    expect((await getStoryAsOwner(s.id)).state).toBe("in_review");
  });
});

/** Recua a hora marcada sem passar pelos triggers (só o dono da base de dados, em teste). */
async function passouAHora(id: string) {
  await ownerDb().begin(async (tx) => {
    await tx`set local session_replication_role = replica`;
    await tx`update stories set scheduled_at = now() - interval '1 minute' where id = ${id}`;
  });
}

async function getStoryAsOwner(id: string) {
  const [row] = await ownerDb()`select state, title from stories where id = ${id}`;
  return row as { state: string; title: string };
}
void getStory;
