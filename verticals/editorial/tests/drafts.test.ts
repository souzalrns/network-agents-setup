// Rascunhos no servidor, conflitos entre duas pessoas, versões, comparação e restauro (D4).
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { agentCtx } from "@/lib/context";
import { closeDb, withCtx } from "@/lib/db";
import { articleOf, compareArticles, discardDraft, getDraft, parseArticle, rescueDraft, restoreVersion, saveDraft, saveVersion } from "@/lib/drafts";
import { createStory, getStory, transition, updateStory } from "@/lib/stories";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

let N: Newsroom;
beforeAll(async () => { N = await newsroom(); });
afterAll(async () => { await closeDb(); await closeOwner(); });

async function emRedacao(title: string) {
  const j = N.as("journalist");
  const s = await createStory(j, { title, sectionId: N.sectionId, propose: true });
  await transition(N.as("editor"), s.id, "pitch_approved");
  await updateStory(N.as("editor"), s.id, { assignee_id: N.users.journalist!.id });
  return transition(j, s.id, "writing");
}
const ler = async (id: string) => (await withCtx(N.as("editor"), (tx) => getStory(tx, id)))!;
const com = (s: Awaited<ReturnType<typeof ler>>, patch: Record<string, unknown>) => ({ ...articleOf(s), ...patch });
const versoes = async (id: string) => (await ownerDb()`select count(*)::int as n from story_versions where story_id = ${id}`)[0]!.n as number;

describe("rascunho no servidor", () => {
  it("o autosave grava sem criar versões; guardar versão cria uma e apaga o rascunho", async () => {
    const s = await emRedacao("Autosave");
    const antes = await versoes(s.id);
    const r1 = await saveDraft(N.as("journalist"), s.id, { rev: null, baseVersion: s.version, fields: com(s, { body: "um" }) });
    expect(r1.status).toBe("saved");
    const r2 = await saveDraft(N.as("journalist"), s.id, { rev: r1.status === "saved" ? r1.rev : 0, baseVersion: s.version, fields: com(s, { body: "um dois" }) });
    expect(r2).toMatchObject({ status: "saved", rev: 2 });
    expect(await versoes(s.id)).toBe(antes);
    const d = (await withCtx(N.as("journalist"), (tx) => getDraft(tx, s.id)))!;
    expect(d.fields.body).toBe("um dois");
    expect(d.lease_user).toBe(N.users.journalist!.id);
    const v = await saveVersion(N.as("journalist"), s.id, d.fields, d.base_version, "primeira versão");
    expect(v.body).toBe("um dois");
    expect(await versoes(s.id)).toBe(antes + 1);
    expect(await withCtx(N.as("journalist"), (tx) => getDraft(tx, s.id))).toBeNull();
  });

  it("duas pessoas no mesmo rascunho: a segunda gravação com revisão antiga é conflito, e nada se perde", async () => {
    const s = await emRedacao("Conflito no rascunho");
    const a = await saveDraft(N.as("journalist"), s.id, { rev: null, baseVersion: s.version, fields: com(s, { body: "texto da jornalista" }) });
    const b = await saveDraft(N.as("editor"), s.id, { rev: null, baseVersion: s.version, fields: com(s, { body: "texto da editora" }) });
    expect(b).toMatchObject({ status: "conflict", reason: "draft" });
    if (b.status === "conflict") expect(b.draft!.fields.body).toBe("texto da jornalista");
    // a editora vê o conflito e decide sobrepor
    const c = await saveDraft(N.as("editor"), s.id, { rev: null, baseVersion: s.version, fields: com(s, { body: "texto da editora" }), force: true });
    expect(c.status).toBe("saved");
    const j = await saveDraft(N.as("journalist"), s.id, { rev: a.status === "saved" ? a.rev : 0, baseVersion: s.version, fields: com(s, { body: "x" }) });
    expect(j.status).toBe("conflict");
  });

  it("guardar versão sobre uma versão que entretanto mudou é recusado (a última gravação não ganha em silêncio)", async () => {
    const s = await emRedacao("Conflito de versão");
    await updateStory(N.as("editor"), s.id, { body: "a editora gravou primeiro" }, "", s.version);
    await expect(saveVersion(N.as("journalist"), s.id, com(s, { body: "a jornalista grava por cima" }), s.version)).rejects.toThrow(/Outra pessoa guardou a versão/);
    expect((await ler(s.id)).body).toBe("a editora gravou primeiro");
    await expect(updateStory(N.as("journalist"), s.id, { body: "y" }, "", s.version)).rejects.toThrow(/Outra pessoa guardou/);
    // o rascunho também avisa: foi começado numa versão antiga
    const r = await saveDraft(N.as("journalist"), s.id, { rev: null, baseVersion: s.version, fields: com(s, { body: "z" }) });
    expect(r).toMatchObject({ status: "conflict", reason: "version" });
  });

  it("só quem pode alterar a peça tem rascunho dela; agentes e leitura não", async () => {
    const s = await emRedacao("Permissões do rascunho");
    await expect(saveDraft(N.as("journalist2"), s.id, { rev: null, baseVersion: s.version, fields: articleOf(s) })).rejects.toThrow();
    await expect(saveDraft(N.as("reviewer"), s.id, { rev: null, baseVersion: s.version, fields: articleOf(s) })).rejects.toThrow();
    await expect(withCtx(agentCtx(N.publicationId, "editorial.editor"), (tx) => tx`insert into story_drafts (story_id, publication_id, base_version, fields)
      values (${s.id}, ${N.publicationId}, 1, '{}')`)).rejects.toThrow();
    await saveDraft(N.as("journalist"), s.id, { rev: null, baseVersion: s.version, fields: articleOf(s) });
    await discardDraft(N.as("journalist"), s.id);
    expect(await withCtx(N.as("journalist"), (tx) => getDraft(tx, s.id))).toBeNull();
  });

  it("os campos que vêm do browser passam por limites e tipos", () => {
    const f = parseArticle((k) => ({ title: "  T  ", tags: "Câmara, Obras ,, ", kind: "outro", body: "x".repeat(300_000) } as Record<string, unknown>)[k]);
    expect(f.title).toBe("T");
    expect(f.tags).toEqual(["câmara", "obras"]);
    expect(f.kind).toBe("news");
    expect(f.body.length).toBe(200_000);
    expect(() => parseArticle((k) => (k === "hero_image_url" ? "javascript:alert(1)" : ""))).toThrow(/https/);
  });
});

describe("versões: comparação e restauro", () => {
  it("compara palavra a palavra e restaurar cria uma versão nova com o conteúdo antigo", async () => {
    const s = await emRedacao("Restauro");
    const v2 = await updateStory(N.as("journalist"), s.id, { body: "A câmara gastou dois milhões.", hero_credit: "Ana" });
    const v3 = await updateStory(N.as("journalist"), s.id, { body: "A câmara gastou vinte milhões.", hero_credit: "Rui" });
    const diff = compareArticles(articleOf(v2), articleOf(v3));
    const body = diff.find((d) => d.key === "body")!;
    expect(body.changed).toBe(true);
    expect(body.parts.filter((p) => p.removed).map((p) => p.value.trim())).toEqual(["dois"]);
    expect(body.parts.filter((p) => p.added).map((p) => p.value.trim())).toEqual(["vinte"]);
    expect(diff.find((d) => d.key === "title")!.changed).toBe(false);

    const r = await restoreVersion(N.as("journalist"), s.id, v2.version, v3.version);
    expect(r.version).toBe(v3.version + 1);
    expect([r.body, r.hero_credit]).toEqual(["A câmara gastou dois milhões.", "Ana"]); // o retrato completo, não só o texto
    const [last] = await ownerDb()`select note from story_versions where story_id = ${s.id} order by version desc limit 1`;
    expect(last!.note).toBe(`Restaurada a versão ${v2.version}`);
    await expect(restoreVersion(N.as("journalist"), s.id, v2.version, v3.version)).rejects.toThrow(/mudou/);
  });

  it("restaurar numa peça aprovada retira a aprovação (é outro conteúdo)", async () => {
    const s = await emRedacao("Restauro aprovado");
    const v = await updateStory(N.as("journalist"), s.id, { body: "Primeiro texto." });
    const w = await updateStory(N.as("journalist"), s.id, { body: "Texto final." });
    await transition(N.as("journalist"), s.id, "in_review");
    await transition(N.as("editor"), s.id, "approved");
    const r = await restoreVersion(N.as("editor"), s.id, v.version, w.version);
    expect([r.state, r.approved_by, r.body]).toEqual(["in_review", null, "Primeiro texto."]);
  });
});

describe("revisão de código: nenhum texto se perde quando outra pessoa guarda", () => {
  it("guardar uma versão não apaga o rascunho de OUTRA pessoa", async () => {
    const s = await emRedacao("Rascunho alheio");
    await saveDraft(N.as("journalist"), s.id, { rev: null, baseVersion: s.version, fields: com(s, { body: "texto da jornalista por guardar" }) });
    await saveVersion(N.as("editor"), s.id, com(s, { body: "a editora guardou outra coisa" }), s.version);
    const d = await withCtx(N.as("journalist"), (tx) => getDraft(tx, s.id));
    expect(d?.fields.body).toBe("texto da jornalista por guardar");
  });

  it("depois de um conflito, o resgate guarda mesmo o texto (sem rascunho, ou com rascunho próprio)", async () => {
    const s = await emRedacao("Resgate");
    await updateStory(N.as("editor"), s.id, { body: "versão nova da editora" }, "", s.version); // a peça avançou
    expect(await rescueDraft(N.as("journalist"), s.id, s.version, com(s, { body: "texto da jornalista" }))).toBe(true);
    const d = (await withCtx(N.as("journalist"), (tx) => getDraft(tx, s.id)))!;
    expect([d.fields.body, d.base_version, d.updated_by]).toEqual(["texto da jornalista", s.version, N.users.journalist!.id]);
    expect(await rescueDraft(N.as("journalist"), s.id, s.version, com(s, { body: "texto revisto" }))).toBe(true);
  });

  it("o resgate nunca escreve por cima do rascunho de outra pessoa", async () => {
    const s = await emRedacao("Resgate alheio");
    await saveDraft(N.as("editor"), s.id, { rev: null, baseVersion: s.version, fields: com(s, { body: "rascunho da editora" }) });
    expect(await rescueDraft(N.as("journalist"), s.id, s.version, com(s, { body: "da jornalista" }))).toBe(false);
    expect((await withCtx(N.as("editor"), (tx) => getDraft(tx, s.id)))!.fields.body).toBe("rascunho da editora");
  });
});
