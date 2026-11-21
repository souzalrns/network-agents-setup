// Publicação agendada sem tarefas frequentes (plano Hobby): a visita publica o que já passou da hora.
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { publishDueOpportunistic } from "@/lib/cron";
import { closeDb } from "@/lib/db";
import { createStory, transition, updateStory } from "@/lib/stories";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

let N: Newsroom;
beforeAll(async () => { N = await newsroom(); });
afterAll(async () => { await closeDb(); await closeOwner(); });

async function agendada(title: string) {
  const j = N.as("journalist");
  const s = await createStory(j, { title, sectionId: N.sectionId, propose: true });
  await transition(N.as("editor"), s.id, "pitch_approved");
  await updateStory(N.as("editor"), s.id, { assignee_id: N.users.journalist!.id });
  await transition(j, s.id, "writing");
  await updateStory(j, s.id, { body: "Texto." });
  await transition(j, s.id, "in_review");
  await transition(N.as("editor"), s.id, "approved");
  return transition(N.as("editor"), s.id, "scheduled", { scheduledAt: new Date(Date.now() + 3_600_000) });
}

describe("publicação oportunista", () => {
  it("publica o que passou da hora, só uma vez por intervalo, e nunca o que ainda não chegou", async () => {
    const hora = await agendada("Já é hora");
    const cedo = await agendada("Ainda não");
    await ownerDb().begin(async (tx) => {
      await tx`set local session_replication_role = replica`;
      await tx`update stories set scheduled_at = now() - interval '1 minute' where id = ${hora.id}`;
    });
    expect(await publishDueOpportunistic(N.publicationId, 60_000)).toEqual([hora.id]);
    expect(await publishDueOpportunistic(N.publicationId, 60_000)).toEqual([]); // dentro do intervalo não volta a consultar
    const st = await ownerDb()`select id, state from stories where id in (${hora.id}, ${cedo.id}) order by title`;
    expect(Object.fromEntries(st.map((r) => [r.id, r.state]))).toEqual({ [hora.id]: "published", [cedo.id]: "scheduled" });
  });
});
