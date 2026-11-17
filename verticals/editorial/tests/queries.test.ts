// Filtros, paginação e actividade da redacção.
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { closeDb, withCtx } from "@/lib/db";
import { countStoriesTx, listActivity, listStoriesTx } from "@/lib/queries";
import { createStory, transition, updateStory } from "@/lib/stories";
import { closeOwner, type Newsroom, newsroom } from "./helpers/fixture";

let N: Newsroom;
beforeAll(async () => {
  N = await newsroom();
  for (let i = 1; i <= 30; i++) {
    const s = await createStory(N.as("journalist"), { title: `Pauta ${String(i).padStart(2, "0")}`, priority: (i % 3) + 1, sectionId: N.sectionId });
    if (i <= 4) await updateStory(N.as("editor"), s.id, { assignee_id: N.users.journalist2!.id });
  }
});
afterAll(async () => { await closeDb(); await closeOwner(); });

describe("pautas: filtros e paginação", () => {
  it("pagina sem repetir nem perder peças e conta o total", async () => {
    const ed = N.as("editor");
    const { total, p1, p2 } = await withCtx(ed, async (tx) => ({
      total: await countStoriesTx(tx, { state: "active" }),
      p1: await listStoriesTx(tx, { state: "active", limit: 25, offset: 0 }),
      p2: await listStoriesTx(tx, { state: "active", limit: 25, offset: 25 }),
    }));
    expect(total).toBe(30);
    expect(p1.length + p2.length).toBe(30);
    expect(new Set([...p1, ...p2].map((r) => r.id)).size).toBe(30);
  });

  it("filtra por pessoa, sem responsável e prioridade", async () => {
    const r = await withCtx(N.as("editor"), async (tx) => ({
      dela: await countStoriesTx(tx, { assignee: N.users.journalist2!.id }),
      sem: await countStoriesTx(tx, { assignee: "none" }),
      alta: await countStoriesTx(tx, { priority: 1 }),
    }));
    expect(r).toEqual({ dela: 4, sem: 26, alta: 10 });
  });
});

describe("actividade", () => {
  it("lista o que aconteceu, filtra por tipo e pessoa e pagina por cursor", async () => {
    const s = await createStory(N.as("journalist"), { title: "Actividade", propose: true, sectionId: N.sectionId });
    await transition(N.as("editor"), s.id, "pitch_approved", { note: "boa ideia" });
    const r = await withCtx(N.as("editor"), async (tx) => ({
      all: await listActivity(tx, { limit: 10 }),
      assign: await listActivity(tx, { type: "assignment" }),
      editor: await listActivity(tx, { actor: N.users.editor!.id, type: "state_change" }),
    }));
    expect(r.all.length).toBe(11); // limit + 1 diz que há mais
    expect(r.assign.length).toBe(4);
    expect(r.editor[0]).toMatchObject({ to_state: "pitch_approved", note: "boa ideia", title: "Actividade" });
    const next = await withCtx(N.as("editor"), (tx) => listActivity(tx, { limit: 10, before: Number(r.all[9]!.id) }));
    expect(Number(next[0]!.id)).toBeLessThan(Number(r.all[9]!.id));
  });
});
