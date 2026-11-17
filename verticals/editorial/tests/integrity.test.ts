// Regressão dos contornos de integridade encontrados na revisão técnica (R1–R8).
// Cada caso corre como a APLICAÇÃO (papel editorial_app, RLS e triggers), com actualizações directas à
// base de dados: é o pior caso, pior do que qualquer formulário. Antes da 0003 todos passavam.
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { systemCtx } from "@/lib/context";
import { closeDb, type Tx, withCtx } from "@/lib/db";
import { createStory, getStory, publishDue, transition, updateStory } from "@/lib/stories";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

let N: Newsroom;
beforeAll(async () => { N = await newsroom(); });
afterAll(async () => { await closeDb(); await closeOwner(); });

/** Peça escrita pelo jornalista e aprovada pela edição, pelo caminho normal. */
async function aprovada(title: string) {
  const j = N.as("journalist");
  const s = await createStory(j, { title, sectionId: N.sectionId, propose: true });
  await transition(N.as("editor"), s.id, "pitch_approved");
  await updateStory(N.as("editor"), s.id, { assignee_id: N.users.journalist!.id });
  await transition(j, s.id, "writing");
  await updateStory(j, s.id, { body: "Texto aprovado.", summary: "Resumo aprovado." });
  await transition(j, s.id, "in_review");
  return transition(N.as("editor"), s.id, "approved");
}

type Rows = Record<string, any>[]; // eslint-disable-line @typescript-eslint/no-explicit-any
const as = (who: string, fn: (tx: Tx) => Promise<Rows>, note = ""): Promise<Rows> => withCtx(N.as(who), fn, note);
const daqui = (h: number) => new Date(Date.now() + h * 3_600_000);

describe("R1–R3, R6: a aprovação fica presa ao conteúdo aprovado", () => {
  it("R1: aprovada → publicada com o texto alterado na mesma actualização é recusado", async () => {
    const s = await aprovada("R1");
    await expect(as("editor", (tx) => tx`update stories set state = 'published', body = 'TEXTO NUNCA APROVADO' where id = ${s.id}`))
      .rejects.toThrow(/passos separados/);
    const depois = (await withCtx(N.as("editor"), (tx) => getStory(tx, s.id)))!;
    expect([depois.state, depois.body]).toEqual(["approved", "Texto aprovado."]);
  });

  it("R2: agendada → publicada com o título alterado é recusado; o sistema também não publica conteúdo mexido", async () => {
    const s = await aprovada("R2");
    await transition(N.as("editor"), s.id, "scheduled", { scheduledAt: daqui(24) });
    await expect(as("editor", (tx) => tx`update stories set state = 'published', title = 'TÍTULO NUNCA APROVADO' where id = ${s.id}`))
      .rejects.toThrow(/passos separados/);
    await expect(withCtx(systemCtx(N.publicationId), (tx) => tx`update stories set state = 'published', title = 'X' where id = ${s.id}`))
      .rejects.toThrow(/sistema só publica/);
    expect((await ownerDb()`select state, title from stories where id = ${s.id}`)[0]).toEqual({ state: "scheduled", title: "R2" });
  });

  it("R3: mudar imagem, endereço ou tipo (patrocinado) de uma peça aprovada retira a aprovação", async () => {
    for (const patch of [{ hero_image_url: "https://exemplo.invalid/outra.jpg" }, { slug: "outro-endereco" }, { kind: "sponsored" },
      { hero_credit: "Outra pessoa" }, { tags: ["nova"] }, { meta_description: "outra" }]) {
      const s = await aprovada(`R3 ${Object.keys(patch)[0]}`);
      const r = await updateStory(N.as("editor"), s.id, patch);
      expect(r.state, JSON.stringify(patch)).toBe("in_review");
      expect(r.approved_by).toBeNull();
      await expect(transition(N.as("editor"), s.id, "published")).rejects.toThrow();
    }
  });

  it("R3b: ninguém escreve os campos da aprovação à mão", async () => {
    const s = await aprovada("R3b");
    await expect(as("editor", (tx) => tx`update stories set approved_by = ${N.users.director!.id} where id = ${s.id}`))
      .rejects.toThrow(/só mudam pelo fluxo/);
    await expect(as("editor", (tx) => tx`update stories set approved_fingerprint = 'x' where id = ${s.id}`))
      .rejects.toThrow(/só mudam pelo fluxo/);
  });

  it("R6: uma peça arquivada não se reescreve, nem se volta a publicar com outro texto", async () => {
    const s = await aprovada("R6");
    await transition(N.as("editor"), s.id, "published");
    await transition(N.as("editor"), s.id, "archived");
    await expect(as("editor", (tx) => tx`update stories set state = 'published', body = 'TEXTO REESCRITO NO ARQUIVO' where id = ${s.id}`))
      .rejects.toThrow(/passos separados/);
    await expect(updateStory(N.as("editor"), s.id, { body: "reescrito" })).rejects.toThrow(/arquivada não se altera/);
    // sem alterações, volta a publicar-se o que estava aprovado
    const r = await transition(N.as("editor"), s.id, "published");
    expect([r.state, r.body]).toEqual(["published", "Texto aprovado."]);
  });

  it("aprovar regista a versão e a impressão digital do que foi aprovado", async () => {
    const s = await aprovada("Impressão digital");
    const [row] = await ownerDb()`select approved_version, approved_fingerprint = editorial.story_fingerprint(s) as igual, version
      from stories s where id = ${s.id}`;
    expect(row).toMatchObject({ igual: true });
    expect(row!.approved_version).toBe(row!.version);
  });
});

describe("R4, R5, R8: afirmações e evidências", () => {
  it("R4: mudar o texto ou a evidência de uma afirmação verificada volta a pô-la por verificar", async () => {
    const s = await aprovada("R4");
    const [c] = await as("editor", (tx) => tx`insert into claims (publication_id, story_id, text, kind, evidence, origin, in_article)
      values (${N.publicationId}, ${s.id}, 'A câmara gastou 2 milhões', 'fact', ${tx.json([{ url: "https://dre.pt/doc-certo" }])}, 'human', true)
      returning id`);
    const [v] = await as("director", (tx) => tx`update claims set verification = 'verified' where id = ${c!.id} returning verification, verified_by`);
    expect(v).toMatchObject({ verification: "verified", verified_by: N.users.director!.id });
    await as("journalist", (tx) => tx`update claims set evidence = ${tx.json([{ url: "https://blog.invalid/rumor" }])},
      text = 'A câmara gastou 20 milhões' where id = ${c!.id}`);
    const [d] = await ownerDb()`select verification, verified_by from claims where id = ${c!.id}`;
    expect(d).toEqual({ verification: "pending", verified_by: null });
    // só acrescentar evidência (o que o formulário fazia) também conta como mudança
    await as("director", (tx) => tx`update claims set verification = 'verified' where id = ${c!.id}`);
    await as("editor", (tx) => tx`update claims set evidence = evidence || ${tx.json([{ url: "https://ine.pt/y" }])} where id = ${c!.id}`);
    expect((await ownerDb()`select verification from claims where id = ${c!.id}`)[0]!.verification).toBe("pending");
    // e com uma afirmação por verificar no artigo, a peça aprovada não se publica
    await expect(transition(N.as("editor"), s.id, "published")).rejects.toThrow(/afirmações por verificar/);
  });

  it("R4b: o verificador não se troca à mão", async () => {
    const s = await aprovada("R4b");
    const [c] = await as("journalist", (tx) => tx`insert into claims (publication_id, story_id, text, kind, evidence, origin)
      values (${N.publicationId}, ${s.id}, 'Facto', 'fact', ${tx.json([{ url: "https://ine.pt/z" }])}, 'human') returning id`);
    await as("editor", (tx) => tx`update claims set verification = 'verified' where id = ${c!.id}`);
    await as("journalist", (tx) => tx`update claims set verified_by = ${N.users.journalist!.id} where id = ${c!.id}`);
    expect((await ownerDb()`select verified_by from claims where id = ${c!.id}`)[0]!.verified_by).toBe(N.users.editor!.id);
  });

  it("R5: uma informação não confirmada acrescentada depois da aprovação impede agendar e publicar", async () => {
    const s = await aprovada("R5");
    await as("journalist", (tx) => tx`insert into claims (publication_id, story_id, text, kind, origin, in_article)
      values (${N.publicationId}, ${s.id}, 'Alegadamente houve desvio', 'unconfirmed', 'human', true)`);
    await expect(transition(N.as("editor"), s.id, "published")).rejects.toThrow(/afirmações por verificar/);
    await expect(transition(N.as("editor"), s.id, "scheduled", { scheduledAt: daqui(2) })).rejects.toThrow(/afirmações por verificar/);
    // retirada do artigo, já se publica
    await as("journalist", (tx) => tx`update claims set in_article = false where story_id = ${s.id}`);
    expect((await transition(N.as("editor"), s.id, "published")).state).toBe("published");
  });

  it("R5b: a publicação agendada também revalida as afirmações e não bloqueia as outras peças", async () => {
    const boa = await aprovada("R5b boa");
    const ma = await aprovada("R5b má");
    for (const s of [boa, ma]) await transition(N.as("editor"), s.id, "scheduled", { scheduledAt: daqui(1) });
    await as("journalist", (tx) => tx`insert into claims (publication_id, story_id, text, kind, origin, in_article)
      values (${N.publicationId}, ${ma.id}, 'Rumor', 'unconfirmed', 'human', true)`);
    await ownerDb().begin(async (tx) => {
      await tx`set local session_replication_role = replica`;
      await tx`update stories set scheduled_at = now() - interval '1 minute' where id in (${boa.id}, ${ma.id})`;
    });
    const publicadas = await publishDue(systemCtx(N.publicationId));
    expect(publicadas).toContain(boa.id);
    expect(publicadas).not.toContain(ma.id);
    expect((await ownerDb()`select state from stories where id = ${ma.id}`)[0]!.state).toBe("scheduled");
  });

  it("R8: com os quatro olhos, quem escreveu a peça ou registou a afirmação não a verifica (D6)", async () => {
    const s = await aprovada("R8");
    await expect(as("journalist", (tx) => tx`insert into claims (publication_id, story_id, text, kind, evidence, verification, origin)
      values (${N.publicationId}, ${s.id}, 'Facto da autora', 'fact', ${tx.json([{ url: "https://ine.pt/x" }])}, 'verified', 'human')`))
      .rejects.toThrow(/não a verifica/);
    const [c] = await as("editor", (tx) => tx`insert into claims (publication_id, story_id, text, kind, evidence, origin)
      values (${N.publicationId}, ${s.id}, 'Facto registado pela edição', 'fact', ${tx.json([{ url: "https://ine.pt/x" }])}, 'human') returning id`);
    await expect(as("editor", (tx) => tx`update claims set verification = 'verified' where id = ${c!.id}`)).rejects.toThrow(/não a verifica/);
    await expect(as("journalist", (tx) => tx`update claims set verification = 'verified' where id = ${c!.id}`)).rejects.toThrow(/não a verifica/);
    // a revisão (fact-checking) verifica, mas não reescreve
    await as("reviewer", (tx) => tx`update claims set verification = 'verified' where id = ${c!.id}`);
    expect((await ownerDb()`select verified_by from claims where id = ${c!.id}`)[0]!.verified_by).toBe(N.users.reviewer!.id);
    await expect(as("reviewer", (tx) => tx`update claims set text = 'outra coisa' where id = ${c!.id}`)).rejects.toThrow(/só marca/);
  });

  it("sem os quatro olhos, a autora pode verificar as suas afirmações", async () => {
    const M = await newsroom({ require_second_reviewer: false });
    const s = await createStory(M.as("journalist"), { title: "Sem quatro olhos" });
    await withCtx(M.as("journalist"), (tx) => tx`insert into claims (publication_id, story_id, text, kind, evidence, verification, origin)
      values (${M.publicationId}, ${s.id}, 'Facto', 'fact', ${tx.json([{ url: "https://ine.pt/x" }])}, 'verified', 'human')`);
    expect((await ownerDb()`select count(*)::int as n from claims where story_id = ${s.id} and verification = 'verified'`)[0]!.n).toBe(1);
  });
});

describe("R7: distribuição", () => {
  async function distribuicao(title: string) {
    const s = await aprovada(title);
    const [d] = await as("editor", (tx) => tx`insert into distribution_items (publication_id, story_id, channel, content, prepared_kind)
      values (${N.publicationId}, ${s.id}, 'instagram', ${tx.json({ text: "aprovado" })}, 'human') returning id`);
    await as("editor", (tx) => tx`update distribution_items set state = 'approved' where id = ${d!.id}`);
    return d!.id as string;
  }

  it("R7: mudar o conteúdo e passar a «enviado» na mesma actualização é recusado", async () => {
    const id = await distribuicao("R7");
    await expect(as("editor", (tx) => tx`update distribution_items set state = 'handed_off', content = ${tx.json({ text: "NUNCA APROVADO" })} where id = ${id}`))
      .rejects.toThrow(/passos separados/);
    expect((await ownerDb()`select state, content from distribution_items where id = ${id}`)[0]).toEqual({ state: "approved", content: { text: "aprovado" } });
  });

  it("R7b: mudar o conteúdo aprovado volta a revisão; o que seguiu para o agendador já não se altera", async () => {
    const id = await distribuicao("R7b");
    await as("journalist", (tx) => tx`update distribution_items set content = ${tx.json({ text: "outro" })} where id = ${id}`);
    expect((await ownerDb()`select state, approved_by from distribution_items where id = ${id}`)[0]).toEqual({ state: "in_review", approved_by: null });
    await as("editor", (tx) => tx`update distribution_items set state = 'approved' where id = ${id}`);
    await as("editor", (tx) => tx`update distribution_items set state = 'handed_off' where id = ${id}`);
    await expect(as("editor", (tx) => tx`update distribution_items set content = ${tx.json({ text: "depois" })} where id = ${id}`))
      .rejects.toThrow(/já seguiu/);
    await expect(as("editor", (tx) => tx`update distribution_items set approved_hash = 'x' where id = ${id}`)).rejects.toThrow(/só muda pelo fluxo/);
  });
});

describe("D5: editar uma peça publicada", () => {
  it("exige a edição e uma nota, conta como nova aprovação e fica registado", async () => {
    const s = await aprovada("D5");
    await transition(N.as("editor"), s.id, "published");
    await expect(updateStory(N.as("journalist"), s.id, { body: "mudança" }, "nota")).rejects.toThrow();
    await expect(updateStory(N.as("director"), s.id, { body: "Texto corrigido." })).rejects.toThrow(/exige uma nota/);
    const r = await updateStory(N.as("director"), s.id, { body: "Texto corrigido." }, "Corrigido o valor do contrato");
    expect(r.state).toBe("published");
    expect(r.approved_by).toBe(N.users.director!.id);
    const [ev] = await ownerDb()`select type, note, actor_user_id from story_events where story_id = ${s.id} and type = 'published_edit'`;
    expect(ev).toEqual({ type: "published_edit", note: "Corrigido o valor do contrato", actor_user_id: N.users.director!.id });
    const [v] = await ownerDb()`select note, snapshot->>'body' as body from story_versions where story_id = ${s.id} order by version desc limit 1`;
    expect(v).toEqual({ note: "Corrigido o valor do contrato", body: "Texto corrigido." });
  });
});

describe("imagens: crédito obrigatório para aprovar", () => {
  it("a imagem principal e as figuras do texto precisam de crédito", async () => {
    const j = N.as("journalist");
    const s = await createStory(j, { title: "Imagem sem crédito", sectionId: N.sectionId, propose: true });
    await transition(N.as("editor"), s.id, "pitch_approved");
    await updateStory(N.as("editor"), s.id, { assignee_id: N.users.journalist!.id });
    await transition(j, s.id, "writing");
    await updateStory(j, s.id, { body: "Texto.\n\n![Ponte](https://exemplo.invalid/p.jpg)\n", hero_image_url: "https://exemplo.invalid/h.jpg" });
    await transition(j, s.id, "in_review");
    await expect(transition(N.as("editor"), s.id, "approved")).rejects.toThrow(/imagem principal precisa de crédito/);
    await updateStory(N.as("editor"), s.id, { hero_credit: "Ana Silva" });
    await expect(transition(N.as("editor"), s.id, "approved")).rejects.toThrow(/figura do texto não tem crédito/);
    await updateStory(N.as("editor"), s.id, { body: 'Texto.\n\n![Ponte](https://exemplo.invalid/p.jpg "Rui Costa")\n' });
    expect((await transition(N.as("editor"), s.id, "approved")).state).toBe("approved");
  });
});
