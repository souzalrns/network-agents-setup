// Postiz com um transporte simulado: só rascunhos, só o aprovado, sem reenvios, e nada sem aprovação humana.
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { closeDb, withCtx } from "@/lib/db";
import { dispatchApproved, type PostizTransport } from "@/lib/postiz";
import { createStory, transition, updateStory } from "@/lib/stories";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

let N: Newsroom;
beforeAll(async () => { N = await newsroom(); });
afterAll(async () => { await closeDb(); await closeOwner(); });

function fake(integrations = [{ id: "int-ig", identifier: "instagram" }]) {
  const sent: { type?: string; posts?: { integration: { id: string }; value: { content: string }[] }[] }[] = [];
  const t: PostizTransport = { integrations: async () => integrations, createPost: async (p) => { sent.push(p as never); return { id: `post-${sent.length}` }; } };
  return { t, sent };
}

async function aprovada(title: string) {
  const j = N.as("journalist");
  const s = await createStory(j, { title, sectionId: N.sectionId, propose: true });
  await transition(N.as("editor"), s.id, "pitch_approved");
  await updateStory(N.as("editor"), s.id, { assignee_id: N.users.journalist!.id });
  await transition(j, s.id, "writing");
  await updateStory(j, s.id, { body: "Texto." });
  await transition(j, s.id, "in_review");
  return transition(N.as("editor"), s.id, "approved");
}
async function item(storyId: string, text: string, approve = true) {
  const [d] = await withCtx(N.as("journalist"), (tx) => tx<{ id: string }[]>`insert into distribution_items (publication_id, story_id, channel, content, prepared_kind)
    values (${N.publicationId}, ${storyId}, 'instagram', ${tx.json({ text, link: "/artigo/x" })}, 'human') returning id`);
  if (approve) await withCtx(N.as("editor"), (tx) => tx`update distribution_items set state = 'approved' where id = ${d!.id}`);
  return d!.id;
}

describe("distribuição para o Postiz", () => {
  it("envia só o aprovado, como rascunho, e não reenvia", async () => {
    const s = await aprovada("Postiz");
    const ok = await item(s.id, "Aprovado para o Instagram");
    const rascunho = await item(s.id, "Ainda por aprovar", false);
    const { t, sent } = fake();
    const r1 = await dispatchApproved(N.as("editor"), { transport: t, siteUrl: "https://exemplo.invalid" });
    expect(r1.map((x) => [x.id, x.status])).toEqual([[ok, "enviado"]]);
    expect(sent).toHaveLength(1);
    expect(sent[0]!.type).toBe("draft");
    expect(sent[0]!.posts![0]!.value[0]!.content).toContain("https://exemplo.invalid/artigo/x");
    const [row] = await ownerDb()`select state, external_ref from distribution_items where id = ${ok}`;
    expect(row!.state).toBe("handed_off");
    expect(row!.external_ref).toMatch(/^sha256:[0-9a-f]{64} postiz:post-1$/);
    expect((await ownerDb()`select state from distribution_items where id = ${rascunho}`)[0]!.state).toBe("draft");
    const r2 = await dispatchApproved(N.as("editor"), { transport: t });
    expect(r2).toEqual([]); // já entregue, não volta a ser escolhido
    expect(sent).toHaveLength(1);
  });

  it("sem credenciais só simula; jornalistas não enviam; peça que voltou a revisão é recusada", async () => {
    const s = await aprovada("Postiz recusas");
    await item(s.id, "Texto aprovado");
    expect((await dispatchApproved(N.as("editor"), { transport: null }))[0]!.status).toBe("simulado");
    await expect(dispatchApproved(N.as("journalist"), { transport: null })).rejects.toThrow(/edição ou a direção/);
    await updateStory(N.as("editor"), s.id, { body: "Texto mudado depois da aprovação." }); // volta a revisão
    const { t, sent } = fake();
    const r = await dispatchApproved(N.as("editor"), { transport: t });
    expect(r.every((x) => x.status === "recusado")).toBe(true);
    expect(sent).toHaveLength(0);
  });

  it("recusa quando há zero ou várias integrações do canal no Postiz", async () => {
    const s = await aprovada("Postiz integrações");
    await item(s.id, "Duas contas");
    const { t, sent } = fake([{ id: "a", identifier: "instagram" }, { id: "b", identifier: "instagram-standalone" }]);
    const r = await dispatchApproved(N.as("editor"), { transport: t });
    expect(r.some((x) => x.status === "recusado" && /2 integrações/.test(x.reason ?? ""))).toBe(true);
    expect(sent).toHaveLength(0);
  });
});
