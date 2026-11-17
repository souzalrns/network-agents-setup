import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { agentCtx } from "@/lib/context";
import { closeDb, withCtx } from "@/lib/db";
import { createStory, updateStory } from "@/lib/stories";
import { titleKey } from "@/lib/text";
import {
  agentDisplayName, Budget, BudgetExceeded, classify, clusterItems, contradictions, type EditReview, extractCheckable,
  type FactcheckReport, GeminiClient, type LlmClient, type LlmRequest, llmFromEnv, PRIMARY_SOURCES, type ResearchDossier,
  reviewText, runAgent, type StorySuggestions, validateOutput,
} from "@/lib/agents";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

let N: Newsroom;
beforeAll(async () => { N = await newsroom(); });
afterAll(async () => { await closeDb(); await closeOwner(); });
afterEach(() => { vi.unstubAllGlobals(); });

/** Modelo falso: devolve o que lhe mandarem e conta as chamadas. */
class FakeLlm implements LlmClient {
  readonly model = "gemini-2.5-flash-lite";
  calls = 0;
  prompts: LlmRequest[] = [];
  constructor(private reply: (req: LlmRequest) => string, private usage = { inputTokens: 800, outputTokens: 200 }) {}
  async generate(req: LlmRequest) {
    this.calls++;
    this.prompts.push(req);
    return { text: this.reply(req), ...this.usage };
  }
}

const sql = () => ownerDb();
async function storyWith(n: Newsroom, fields: { title: string; body: string; summary?: string; subtitle?: string; angle?: string; tags?: string[] }) {
  const j = n.as("journalist");
  const s = await createStory(j, { title: fields.title, sectionId: n.sectionId, angle: fields.angle });
  return updateStory(j, s.id, { body: fields.body, summary: fields.summary ?? "", subtitle: fields.subtitle ?? "", tags: fields.tags ?? [] });
}
const snapshot = async (id: string) => (await sql()`
  select title, subtitle, summary, body, version, state, updated_at, seo_title, meta_description from stories where id = ${id}`)[0];
const auditOf = (runId: string) => sql()<{ action: string; actor_kind: string; payload: Record<string, unknown> }[]>`
  select action, actor_kind, payload from audit_log where entity_id = ${runId} order by id`;
const urlsIn = (v: unknown) => [...JSON.stringify(v).matchAll(/https?:\/\/[^"\s\\]+/g)].map((m) => m[0]);

// ================================================================ edição assistida
const SENSATIONAL_BODY = [
  "O caso é chocante e já é um escândalo na cidade. Toda a gente sabe o que se passou.",
  "«Não vamos aceitar este tipo de decisões sem que nos expliquem nada», ouviu-se na sala.",
  "«Vamos recorrer da decisão em tribunal», disse o presidente da associação, Rui Costa.",
  "A obra custou 2,3 milhões de euros e atrasou 40% face ao previsto.",
  Array.from({ length: 130 }, (_, i) => `palavra${i}`).join(" ") + ".",
].join("\n\n");

describe("edição assistida (editorial.editor)", () => {
  it("encontra linguagem sensacionalista, citações sem atribuição, parágrafos longos, números sem fonte e campos em falta", () => {
    const f = reviewText({ title: "x".repeat(95), subtitle: "", summary: "", body: SENSATIONAL_BODY, seo_title: "", meta_description: "" });
    const rules = f.map((x) => x.rule);
    expect(rules).toContain("title.length");
    expect(rules).toContain("summary.missing");
    expect(rules).toContain("seo.title_missing");
    expect(rules).toContain("readability.long_paragraph");
    expect(f.filter((x) => x.rule === "wording.loaded").map((x) => x.suggestion).join(" ")).toMatch(/chocante.*escandalo|escandalo.*chocante/s);
    expect(rules).toContain("wording.generalization");
    const unattributed = f.filter((x) => x.rule === "quote.unattributed");
    expect(unattributed).toHaveLength(1);
    expect(unattributed[0]!.excerpt).toContain("Não vamos aceitar");
    expect(f.find((x) => x.rule === "number.unsourced")?.excerpt).toContain("2,3 milhões");
  });

  it("«polémica» atribuída e números com fonte não dão aviso", () => {
    const f = reviewText({ title: "Plano de mobilidade", subtitle: "s", summary: "r", seo_title: "t", meta_description: "d",
      body: "A medida é uma polémica, disse a vereadora Ana Lopes.\n\nSegundo o INE, a taxa de desemprego foi de 6,5% em 2024." });
    expect(f.map((x) => x.rule)).not.toContain("wording.loaded");
    expect(f.map((x) => x.rule)).not.toContain("number.unsourced");
  });

  it("as palavras de quem é citado não contam como linguagem do jornalista", () => {
    const f = reviewText({ title: "Comerciantes 12 milhões", subtitle: "s", summary: "r", seo_title: "t", meta_description: "d",
      body: "\"Ninguém nos ouviu durante este processo vergonhoso\", lamentam os comerciantes da Baixa." });
    expect(f.map((x) => x.rule)).not.toContain("wording.generalization");
    expect(f.map((x) => x.rule)).not.toContain("wording.loaded");
    expect(f.map((x) => x.rule)).not.toContain("quote.unattributed");
    expect(f.map((x) => x.rule)).not.toContain("number.unsourced"); // o título não cita fontes
  });

  it("revê a peça sem nunca a alterar, guarda uma proposta e regista a execução", async () => {
    const s = await storyWith(N, { title: "Obra atrasada no centro", body: SENSATIONAL_BODY });
    await withCtx(N.as("journalist"), (tx) => tx`insert into claims (publication_id, story_id, text, kind, in_article) values
      (${N.publicationId}, ${s.id}, 'O autarca terá recebido dinheiro', 'unconfirmed', true),
      (${N.publicationId}, ${s.id}, 'A obra custou 2,3 milhões de euros', 'fact', true)`);
    const before = await snapshot(s.id);
    const versions = (await sql()`select count(*)::int as n from story_versions where story_id = ${s.id}`)[0]!.n;

    const r = await runAgent(N.publicationId, "editorial.editor", { storyId: s.id }, { llm: null });
    expect(r.status).toBe("completed");
    const out = r.output as EditReview;
    expect(out.proposal).toBe(true);
    expect(out.findings.map((x) => x.rule)).toEqual(expect.arrayContaining(["claim.unconfirmed_in_article", "claim.fact_unverified"]));
    expect(out.counts.blocker).toBeGreaterThanOrEqual(2);
    expect(out.adaptations.draft).toBe(true);
    expect(out.adaptations.instagram_carousel.slides.length).toBeGreaterThan(1);
    expect(out.adaptations.reel_script.target_seconds).toEqual({ min: 45, max: 60 });
    expect(out.llm.status).toBe("not_configured");
    expect(out.cost).toEqual({ calls: 0, input_tokens: 0, output_tokens: 0, usd_estimate: 0 });

    // a peça está exactamente igual
    expect(await snapshot(s.id)).toEqual(before);
    expect((await sql()`select count(*)::int as n from story_versions where story_id = ${s.id}`)[0]!.n).toBe(versions);

    const [row] = await sql()`select status, kind, agent_id, run_id, cost from agent_outputs where id = ${r.outputId}`;
    expect(row).toMatchObject({ status: "proposed", kind: "edit_review", agent_id: "editorial.editor", run_id: r.runId });
    const [note] = await sql()`select author_kind, kind, author_id, body from comments where story_id = ${s.id}`;
    expect(note).toMatchObject({ author_kind: "agent", kind: "agent_note", author_id: null });
    expect(note!.body).toContain(r.outputId!);
    const audit = await auditOf(r.runId);
    expect(audit.map((a) => a.action)).toEqual(["agent.run.start", "agent.run.finish"]);
    expect(audit.every((a) => a.actor_kind === "agent")).toBe(true);
    const [ev] = await sql()`select type, actor_kind from story_events where story_id = ${s.id} and type = 'agent_output'`;
    expect(ev).toMatchObject({ actor_kind: "agent" });
  });

  it("um agente não consegue alterar, aprovar nem publicar uma peça, mesmo directamente na base de dados", async () => {
    const s = await storyWith(N, { title: "Intocável", body: "Texto." });
    const before = await snapshot(s.id);
    const ctx = agentCtx(N.publicationId, "editorial.editor");
    const upd = await withCtx(ctx, (tx) => tx`update stories set title = 'mudado', state = 'published' where id = ${s.id}`);
    expect(upd.count).toBe(0);
    expect(await snapshot(s.id)).toEqual(before);
    await expect(withCtx(ctx, (tx) => tx`insert into agent_outputs (publication_id, story_id, agent_id, kind, payload, status)
      values (${N.publicationId}, ${s.id}, 'editorial.editor', 'edit_review', '{}', 'accepted')`)).rejects.toMatchObject({ code: "42501" });
  });

  it("o passo com modelo só acrescenta sugestões presas a excertos literais", async () => {
    const s = await storyWith(N, { title: "Com modelo", body: "A câmara aprovou o plano ontem à noite numa reunião longa." });
    const llm = new FakeLlm(() => JSON.stringify({ suggestions: [
      { rule: "clareza", excerpt: "aprovou o plano ontem à noite", suggestion: "Indicar o dia da reunião em vez de «ontem»." }] }));
    const r = await runAgent(N.publicationId, "editorial.editor", { storyId: s.id }, { llm });
    const out = r.output as EditReview;
    expect(r.status).toBe("completed");
    expect(out.llm.status).toBe("used");
    expect(out.suggestions).toEqual([expect.objectContaining({ origin: "llm", excerpt: "aprovou o plano ontem à noite" })]);
    expect(out.cost.calls).toBe(1);
    expect(out.cost.input_tokens).toBe(800);
    expect(out.cost.usd_estimate).toBeGreaterThan(0);
    expect(llm.prompts[0]!.system).toMatch(/APENAS o material fornecido/);
    expect(llm.prompts[0]!.system).toMatch(/unconfirmed/);
    expect(llm.prompts[0]!.system).toMatch(/Nunca inventes citações/);
    expect((await snapshot(s.id))!.body).toBe("A câmara aprovou o plano ontem à noite numa reunião longa.");
  });

  it("uma resposta do modelo que não é JSON válido (ou inventa excertos) é recusada e registada", async () => {
    const s = await storyWith(N, { title: "Modelo avariado", body: "Texto simples da peça." });
    const bad = new FakeLlm(() => "Claro! Aqui tens as sugestões: {nada disto é json");
    const r = await runAgent(N.publicationId, "editorial.editor", { storyId: s.id }, { llm: bad });
    expect(r.status).toBe("completed");
    const out = r.output as EditReview;
    expect(out.llm.status).toBe("rejected");
    expect(out.llm.reason).toMatch(/não é JSON válido/);
    expect(out.suggestions).toEqual([]);
    expect(out.cost.calls).toBe(1); // a chamada conta para o custo, mesmo recusada
    expect((await auditOf(r.runId)).map((a) => a.action)).toEqual(["agent.run.start", "agent.llm.rejected", "agent.run.finish"]);
    const [stored] = await sql()`select payload from agent_outputs where id = ${r.outputId}`;
    expect(JSON.stringify(stored!.payload)).not.toContain("nada disto");

    const invented = new FakeLlm(() => JSON.stringify({ suggestions: [{ rule: "x", excerpt: "frase que não existe", suggestion: "y" }] }));
    const r2 = await runAgent(N.publicationId, "editorial.editor", { storyId: s.id }, { llm: invented });
    expect((r2.output as EditReview).llm).toMatchObject({ status: "rejected" });
    expect((r2.output as EditReview).suggestions).toEqual([]);
  });

  it("orçamento ultrapassado pára a execução com o motivo registado, sem chamar o modelo", async () => {
    const s = await storyWith(N, { title: "Orçamento", body: "Texto da peça." });
    const llm = new FakeLlm(() => JSON.stringify({ suggestions: [] }));
    const r = await runAgent(N.publicationId, "editorial.editor", { storyId: s.id }, { llm, limits: { maxUsd: 0.000001 } });
    expect(r.status).toBe("stopped");
    expect(r.reason).toMatch(/orçamento/);
    expect(llm.calls).toBe(0);
    const audit = await auditOf(r.runId);
    expect(audit.map((a) => a.action)).toEqual(["agent.run.start", "agent.run.stopped"]);
    expect(audit[1]!.payload.reason).toMatch(/orçamento/);

    const r2 = await runAgent(N.publicationId, "editorial.editor", { storyId: s.id }, { llm, limits: { maxCalls: 0 } });
    expect(r2).toMatchObject({ status: "stopped" });
    expect(r2.reason).toMatch(/limite de chamadas/);
    expect(llm.calls).toBe(0);
  });

  it("o orçamento conta chamadas e custo e recusa a chamada que o ultrapassaria", () => {
    const b = new Budget({ maxCalls: 2, maxOutputTokens: 1000, maxUsd: 0.01 });
    b.reserve("gemini-2.5-flash-lite", "x".repeat(1000));
    b.record("gemini-2.5-flash-lite", { inputTokens: 1_000, outputTokens: 1_000 });
    expect(b.cost).toMatchObject({ calls: 1, input_tokens: 1000, output_tokens: 1000 });
    expect(b.cost.usd_estimate).toBeCloseTo(0.0005, 6);
    b.record("gemini-2.5-flash-lite", { inputTokens: 1, outputTokens: 1 });
    expect(() => b.reserve("gemini-2.5-flash-lite", "x")).toThrow(BudgetExceeded);
  });
});

// ================================================================ verificação
const FC = {
  statement: "O presidente da câmara, João Silva, disse que a obra custou 2 milhões de euros.",
  statement2: "Segundo o INE, a taxa de desemprego subiu para 6,5% em 2024.",
  inference: "A nova ponte poderá custar 3 milhões de euros ao município.",
  unconfirmed: "O vereador terá recebido 50 mil euros de uma construtora, segundo fontes não identificadas.",
  unconfirmed2: "Alegadamente, o contrato foi assinado em março sem concurso.",
  fact: "A Câmara Municipal de Braga aprovou um orçamento de 120 milhões de euros para 2025.",
  fact2: "O contrato foi assinado a 3 de março de 2024.",
};

describe("verificação (editorial.factcheck)", () => {
  it("classifica os quatro tipos em frases portuguesas", () => {
    expect(classify(FC.statement)).toMatchObject({ kind: "statement", attributed_to: "João Silva" });
    expect(classify(FC.statement2)).toMatchObject({ kind: "statement", attributed_to: "o INE" });
    expect(classify(FC.inference).kind).toBe("inference");
    expect(classify("O projecto pode vir a ser chumbado na assembleia.").kind).toBe("inference");
    expect(classify(FC.unconfirmed).kind).toBe("unconfirmed");
    expect(classify(FC.unconfirmed2).kind).toBe("unconfirmed");
    expect(classify("Há rumores de uma remodelação no Governo.").kind).toBe("unconfirmed");
    expect(classify(FC.fact).kind).toBe("fact");
    expect(classify(FC.fact2).kind).toBe("fact");
    expect(classify("«Vamos avançar já em maio», afirmou a ministra da Saúde.")).toMatchObject({ kind: "statement", attributed_to: "a ministra da Saúde" });
    // um rumor sem números também é verificável; uma frase sem nada para verificar fica de fora
    const sents = extractCheckable({ title: "t", subtitle: "", summary: "",
      body: "Alegadamente, o projecto terá sido alterado à última hora. A praça é bonita." });
    expect(sents).toEqual(["Alegadamente, o projecto terá sido alterado à última hora."]);
  });

  it("assinala números diferentes para a mesma entidade e métrica", () => {
    const c = contradictions([
      "A Câmara Municipal de Braga contratou 120 trabalhadores em 2024.",
      "No total, a Câmara Municipal de Braga contratou 150 trabalhadores em 2024, segundo o relatório.",
    ]);
    expect(c).toHaveLength(1);
    expect(c[0]).toMatchObject({ entity: "Câmara Municipal de Braga", metric: "trabalhadores" });
    expect(c[0]!.values).toEqual(["120", "150"]);
  });

  it("cria só afirmações pendentes, de origem agente, sem duplicar, e nunca verifica nada", async () => {
    const s = await storyWith(N, { title: "Contratos na câmara", body: Object.values(FC).join(" ") + "\n\nA praça é bonita." });
    // a mesma notícia em três meios: repetição, não verificação
    for (const outlet of ["Jornal A", "Rádio B", "Diário C"]) {
      await withCtx(N.as("journalist"), (tx) => tx`insert into story_refs (publication_id, story_id, kind, url, title, credit, added_by)
        values (${N.publicationId}, ${s.id}, 'article', ${`https://${outlet.replace(/\s/g, "").toLowerCase()}.example/vereador`},
                'Vereador terá recebido 50 mil euros de construtora', ${outlet}, ${N.users.journalist!.id})`);
    }
    await withCtx(N.as("journalist"), (tx) => tx`insert into story_refs (publication_id, story_id, kind, url, title, added_by)
      values (${N.publicationId}, ${s.id}, 'document', 'https://diariodarepublica.pt/orcamento-braga', 'Orçamento da Câmara Municipal de Braga 2025', ${N.users.journalist!.id})`);

    const r = await runAgent(N.publicationId, "editorial.factcheck", { storyId: s.id }, { llm: null });
    expect(r.status).toBe("completed");
    const out = r.output as FactcheckReport;
    const byText = (t: string) => out.claims.find((c) => c.text === t)!;
    expect(byText(FC.statement)).toMatchObject({ kind: "statement", attributed_to: "João Silva", verification: "pending", created: true });
    expect(byText(FC.inference).kind).toBe("inference");
    expect(byText(FC.unconfirmed).kind).toBe("unconfirmed");
    expect(byText(FC.fact).kind).toBe("fact");
    expect(out.claims.find((c) => c.text === "A praça é bonita.")).toBeUndefined();
    // documento: evidência candidata; artigos de outros meios: só repetição
    expect(byText(FC.fact).evidence).toEqual([expect.objectContaining({ url: "https://diariodarepublica.pt/orcamento-braga", relation: "candidate" })]);
    expect(byText(FC.unconfirmed).repetition).toHaveLength(3);
    expect(byText(FC.unconfirmed).evidence).toEqual([]);
    expect(out.rules.join(" ")).toMatch(/repetição.*nunca/);

    const rows = await sql()<{ kind: string; verification: string; origin: string; in_article: boolean; verified_by: string | null; attributed_to: string }[]>`
      select kind, verification, origin, in_article, verified_by, attributed_to from claims where story_id = ${s.id}`;
    expect(rows.length).toBe(out.claims.length);
    expect(rows.every((c) => c.verification === "pending" && c.origin === "agent" && c.verified_by === null && !c.in_article)).toBe(true);
    expect(rows.filter((c) => c.kind === "statement").every((c) => c.attributed_to.length > 0)).toBe(true);

    // segunda execução: não duplica e a repetição continua a não verificar
    const r2 = await runAgent(N.publicationId, "editorial.factcheck", { storyId: s.id }, { llm: null });
    const out2 = r2.output as FactcheckReport;
    expect(out2.claims.every((c) => !c.created && c.verification === "pending")).toBe(true);
    expect(out2.claims.find((c) => c.text === FC.unconfirmed)!.kind).toBe("unconfirmed");
    expect((await sql()`select count(*)::int as n from claims where story_id = ${s.id}`)[0]!.n).toBe(rows.length);
  });

  it("a base de dados recusa que um agente marque uma afirmação como verificada", async () => {
    const s = await storyWith(N, { title: "Verificar", body: "A obra custou 5 milhões de euros." });
    const ctx = agentCtx(N.publicationId, "editorial.factcheck");
    await expect(withCtx(ctx, (tx) => tx`insert into claims (publication_id, story_id, text, kind, evidence, verification, origin, verified_by, verified_at)
      values (${N.publicationId}, ${s.id}, 'A obra custou 5 milhões', 'fact', ${tx.json([{ url: "https://x.example", title: "t" }])},
              'verified', 'agent', ${N.users.editor!.id}, now())`)).rejects.toThrow(/só uma pessoa marca uma afirmação como verificada/);
    const r = await runAgent(N.publicationId, "editorial.factcheck", { storyId: s.id }, { llm: null });
    const id = (r.output as FactcheckReport).claims[0]!.claim_id!;
    const upd = await withCtx(ctx, (tx) => tx`update claims set verification = 'verified' where id = ${id}`);
    expect(upd.count).toBe(0);
    expect((await sql()`select verification from claims where id = ${id}`)[0]!.verification).toBe("pending");
  });

  it("a segunda opinião do modelo fica no relatório e não muda as afirmações", async () => {
    const s = await storyWith(N, { title: "Segunda opinião", body: FC.fact });
    const llm = new FakeLlm(() => JSON.stringify({ claims: [{ text: FC.fact, kind: "inference", attributed_to: "", note: "valor previsto" }] }));
    const r = await runAgent(N.publicationId, "editorial.factcheck", { storyId: s.id }, { llm });
    const out = r.output as FactcheckReport;
    expect(out.second_opinion).toEqual([expect.objectContaining({ kind: "inference" })]);
    expect(out.claims[0]!.kind).toBe("fact");
  });
});

// ================================================================ investigação
async function feedSource(n: Newsroom, name: string, tier = "media", category = "") {
  const [r] = await sql()<{ id: string }[]>`insert into feed_sources (publication_id, name, feed_url, tier, category)
    values (${n.publicationId}, ${name}, ${`https://${name.replace(/\W/g, "").toLowerCase()}-${Math.random().toString(36).slice(2, 8)}.example/rss`}, ${tier}, ${category})
    returning id`;
  return r!.id;
}
async function feedItem(n: Newsroom, sourceId: string, title: string, o: { url?: string; hoursAgo?: number; topics?: string[];
  duplicateOf?: string; status?: string; relevance?: number; excerpt?: string } = {}) {
  const url = o.url ?? `https://noticias.example/${Math.random().toString(36).slice(2, 10)}`;
  const when = new Date(Date.now() - (o.hoursAgo ?? 2) * 3_600_000);
  const [r] = await sql()<{ id: string }[]>`insert into feed_items (publication_id, feed_source_id, url, url_key, title, title_key,
      excerpt, published_at, duplicate_of, relevance, topics, status)
    values (${n.publicationId}, ${sourceId}, ${url}, ${url.replace(/^https?:\/\//, "")}, ${title}, ${titleKey(title)}, ${o.excerpt ?? ""},
            ${when}, ${o.duplicateOf ?? null}, ${o.relevance ?? 0}, ${o.topics ?? []}, ${o.status ?? "new"}) returning id`;
  return { id: r!.id, url };
}

describe("investigação (editorial.research)", () => {
  it("o dossier só tem endereços do material fornecido e fontes primárias marcadas «por consultar»", async () => {
    const R = await newsroom();
    const s = await storyWith(R, { title: "Contratos de limpeza urbana em Braga", angle: "Quem ganhou os ajustes directos da câmara",
      body: "A câmara adjudicou três contratos por ajuste directo.", tags: ["autarquias"] });
    await withCtx(R.as("journalist"), (tx) => tx`update stories set to_confirm = 'Valor total dos contratos; datas de adjudicação' where id = ${s.id}`);
    await withCtx(R.as("journalist"), (tx) => tx`insert into story_refs (publication_id, story_id, kind, url, title, added_by)
      values (${R.publicationId}, ${s.id}, 'document', 'https://www.base.gov.pt/contrato/123', 'Contrato 123', ${R.users.journalist!.id})`);
    const src = await feedSource(R, "Jornal do Minho");
    const near = await feedItem(R, src, "Braga: contratos de limpeza urbana por ajuste directo", { hoursAgo: 30, excerpt: "A câmara..." });
    const topic = await feedItem(R, src, "Eleições autárquicas: o que muda", { hoursAgo: 10, topics: ["autarquias"] });
    const far = await feedItem(R, src, "Festival de jazz regressa ao Porto", { hoursAgo: 5 });

    const r = await runAgent(R.publicationId, "editorial.research", { storyId: s.id }, { llm: null });
    expect(r.status).toBe("completed");
    const out = r.output as ResearchDossier;
    const provided = new Set(["https://www.base.gov.pt/contrato/123", near.url, topic.url]);
    const primary = new Set(PRIMARY_SOURCES.map((p) => p.url));
    for (const u of urlsIn(out)) expect(provided.has(u) || primary.has(u), u).toBe(true);
    expect(urlsIn(out)).not.toContain(far.url);
    expect(out.sources_used.sort()).toEqual([...provided].sort());
    expect(out.primary_sources.length).toBeGreaterThan(0);
    expect(out.primary_sources.every((p) => p.status === "por consultar" && primary.has(p.url))).toBe(true);
    expect(out.primary_sources.map((p) => p.url)).toContain("https://www.base.gov.pt");
    expect(out.timeline.map((t) => t.url)).toEqual([near.url, topic.url]); // por data
    expect(out.open_questions.join(" ")).toMatch(/Por confirmar: Valor total dos contratos/);
    expect(out.interview_questions.length).toBeGreaterThan(3);
    expect(out.summary).toBeNull();
  });

  it("o resumo do modelo só cita o material; um endereço inventado faz recusar a resposta", async () => {
    const R = await newsroom();
    const s = await storyWith(R, { title: "Plano de mobilidade de Braga", body: "Texto." });
    const src = await feedSource(R, "Rádio Braga");
    const it1 = await feedItem(R, src, "Braga apresenta plano de mobilidade", { excerpt: "Plano com novas ciclovias." });
    const good = new FakeLlm(() => JSON.stringify({ summary: "A câmara apresentou um plano com ciclovias.", points: [
      { text: "O plano inclui novas ciclovias.", kind: "fact", attributed_to: "", items: [1] },
      { text: "O custo não é conhecido.", kind: "unconfirmed", attributed_to: "", items: [] }] }));
    const r = await runAgent(R.publicationId, "editorial.research", { storyId: s.id }, { llm: good });
    const out = r.output as ResearchDossier;
    expect(out.llm.status).toBe("used");
    expect(out.summary!.points[0]).toMatchObject({ kind: "fact", evidence: [expect.objectContaining({ url: it1.url, relation: "cited" })] });
    expect(out.summary!.points[1]).toMatchObject({ kind: "unconfirmed", evidence: [] });

    const invented = new FakeLlm(() => JSON.stringify({ summary: "Ver https://inventado.example/x", points: [] }));
    const r2 = await runAgent(R.publicationId, "editorial.research", { storyId: s.id }, { llm: invented });
    expect((r2.output as ResearchDossier).summary).toBeNull();
    expect((r2.output as ResearchDossier).llm.status).toBe("rejected");
    expect(urlsIn(r2.output)).not.toContain("https://inventado.example/x");
    const unsupported = new FakeLlm(() => JSON.stringify({ summary: "Resumo.", points: [{ text: "Algo sem fonte.", kind: "fact", attributed_to: "", items: [] }] }));
    const r3 = await runAgent(R.publicationId, "editorial.research", { storyId: s.id }, { llm: unsupported });
    expect((r3.output as ResearchDossier).llm.status).toBe("rejected");
  });
});

// ================================================================ radar
describe("sugestões do radar (editorial.radar)", () => {
  it("junta duplicados e títulos semelhantes, ordena e só cria ideias quando pedido", async () => {
    const R = await newsroom();
    const [a, b, c, inst] = [await feedSource(R, "Jornal A"), await feedSource(R, "Rádio B"), await feedSource(R, "Diário C"),
      await feedSource(R, "Câmara de Braga", "institutional")];
    const first = await feedItem(R, a, "Câmara de Braga aprova novo plano de mobilidade", { topics: ["local"], relevance: 3 });
    await feedItem(R, b, "Braga aprova novo plano de mobilidade na câmara", { topics: ["local"] });
    await feedItem(R, c, "Câmara de Braga aprova plano de mobilidade", { duplicateOf: first.id });
    await feedItem(R, inst, "Plano de mobilidade de Braga aprovado pela câmara", { topics: ["local"] });
    await feedItem(R, a, "Festival de jazz regressa ao Porto", { hoursAgo: 1 });
    const old = await feedItem(R, b, "Notícia antiga sobre mobilidade em Braga", { hoursAgo: 24 * 10 });
    const dismissed = await feedItem(R, c, "Câmara de Braga aprova novo plano de mobilidade urbana", { status: "dismissed" });
    const storiesBefore = (await sql()`select count(*)::int as n from stories where publication_id = ${R.publicationId}`)[0]!.n;

    const r = await runAgent(R.publicationId, "editorial.radar", {}, { llm: null, topN: 5 });
    expect(r.status).toBe("completed");
    const out = r.output as StorySuggestions;
    expect(out.clusters.length).toBe(2);
    const top = out.clusters[0]!;
    expect(top.sources_count).toBe(4);
    expect(top.item_urls).toHaveLength(4);
    expect(top.item_urls).not.toContain(old.url);
    expect(top.item_urls).not.toContain(dismissed.url);
    expect(top.title).toBe("Plano de mobilidade de Braga aprovado pela câmara"); // a fonte institucional dá o título
    expect(top).toMatchObject({ suggested_section: "Local", suggested_section_id: R.sectionId }); // texto: a página mostra-o tal como está
    expect(top.why).toMatch(/4 meio/);
    expect(top.idea_story_id).toBeNull();
    expect(out.clusters[1]!.sources_count).toBe(1);
    expect((await sql()`select count(*)::int as n from stories where publication_id = ${R.publicationId}`)[0]!.n).toBe(storiesBefore);
    const [row] = await sql()`select story_id, kind from agent_outputs where id = ${r.outputId}`;
    expect(row).toMatchObject({ story_id: null, kind: "story_suggestions" });

    const r2 = await runAgent(R.publicationId, "editorial.radar", {}, { llm: null, topN: 1, createIdeas: true });
    const idea = (r2.output as StorySuggestions).clusters[0]!;
    expect(idea.idea_story_id).toBeTruthy();
    const [st] = await sql()`select state, origin, created_by, section_id, title from stories where id = ${idea.idea_story_id}`;
    expect(st).toMatchObject({ state: "idea", origin: "agent", created_by: null, section_id: R.sectionId });
    const refs = await sql()`select added_kind, url from story_refs where story_id = ${idea.idea_story_id}`;
    expect(refs.length).toBe(4);
    expect(refs.every((x) => x.added_kind === "agent")).toBe(true);
    // sem ideias repetidas
    const r3 = await runAgent(R.publicationId, "editorial.radar", {}, { llm: null, topN: 1, createIdeas: true });
    expect((r3.output as StorySuggestions).clusters[0]!.idea_story_id).toBe(idea.idea_story_id);
    expect((await sql()`select count(*)::int as n from stories where publication_id = ${R.publicationId}`)[0]!.n).toBe(storiesBefore + 1);
  });

  it("agrupa por semelhança de título e pelo original de um duplicado (função pura)", () => {
    const mk = (id: string, title: string, dup: string | null = null) => ({ id, url: `https://x.example/${id}`, title, title_key: titleKey(title),
      published_at: new Date(), fetched_at: new Date(), duplicate_of: dup, relevance: 0, topics: [], source_id: id, source_name: id,
      tier: "media" as const, category: "" });
    const groups = clusterItems([mk("1", "Greve dos professores marcada para sexta"), mk("2", "Professores marcam greve para sexta"),
      mk("3", "Texto completamente diferente", "1"), mk("4", "Chuva forte no Algarve")]);
    expect(groups.map((g) => g.map((i) => i.id).sort())).toEqual(expect.arrayContaining([["1", "2", "3"], ["4"]]));
  });
});

// ================================================================ fronteiras
describe("fronteiras dos agentes", () => {
  it("um agente não lê fontes, ligações peça-fonte, comentários nem utilizadores", async () => {
    const s = await storyWith(N, { title: "Com fontes", body: "Texto." });
    await withCtx(N.as("journalist"), async (tx) => {
      const [src] = await tx<{ id: string }[]>`insert into sources (publication_id, name, contact, owner_id)
        values (${N.publicationId}, 'Fonte confidencial', '912 000 000', ${N.users.journalist!.id}) returning id`;
      await tx`insert into story_sources (publication_id, story_id, source_id) values (${N.publicationId}, ${s.id}, ${src!.id})`;
      await tx`insert into comments (publication_id, story_id, author_id, body) values (${N.publicationId}, ${s.id}, ${N.users.journalist!.id}, 'nota interna')`;
    });
    const ctx = agentCtx(N.publicationId, "editorial.research");
    for (const t of ["sources", "story_sources", "comments", "users"]) {
      const rows = await withCtx(ctx, (tx) => tx.unsafe(`select 1 from ${t}`));
      expect(rows.length, t).toBe(0);
      expect((await sql().unsafe(`select count(*)::int as n from ${t}`))[0]!.n, t).toBeGreaterThan(0);
    }
    const r = await runAgent(N.publicationId, "editorial.research", { storyId: s.id }, { llm: null });
    expect(JSON.stringify(r.output)).not.toMatch(/Fonte confidencial|912 000 000|nota interna/);
  });

  it("as propostas ficam isoladas por publicação", async () => {
    const B = await newsroom();
    const sA = await storyWith(N, { title: "Só da A", body: "O caso é chocante." });
    const r = await runAgent(B.publicationId, "editorial.editor", { storyId: sA.id }, { llm: null });
    expect(r.status).toBe("failed");
    expect(r.reason).toMatch(/não encontrei a peça/);
    expect((await auditOf(r.runId)).map((a) => a.action)).toEqual(["agent.run.start", "agent.run.failed"]);
    const ok = await runAgent(N.publicationId, "editorial.editor", { storyId: sA.id }, { llm: null });
    expect(ok.status).toBe("completed");
    const seenByB = await withCtx(agentCtx(B.publicationId, "editorial.editor"), (tx) => tx<{ publication_id: string }[]>`select publication_id from agent_outputs`);
    expect(seenByB.every((x) => x.publication_id === B.publicationId)).toBe(true);
    expect((await sql()`select count(*)::int as n from agent_outputs where publication_id = ${B.publicationId}`)[0]!.n).toBe(0);
    // o radar de B não vê os itens de A
    const srcA = await feedSource(N, "Fonte da A");
    await feedItem(N, srcA, "Notícia só da publicação A");
    const radarB = await runAgent(B.publicationId, "editorial.radar", {}, { llm: null });
    expect((radarB.output as StorySuggestions).items_considered).toBe(0);
  });

  it("nomes de apresentação vêm da publicação, com nomes neutros por omissão", async () => {
    expect(agentDisplayName({ agent_names: {} }, "editorial.factcheck")).toBe("Verificação");
    expect(agentDisplayName(null, "editorial.editor")).toBe("Edição assistida");
    const P = await newsroom();
    await sql()`update publications set agent_names = ${sql().json({ "editorial.editor": "Revisora Ana" })} where id = ${P.publicationId}`;
    const s = await storyWith(P, { title: "Nome", body: "Texto." });
    const r = await runAgent(P.publicationId, "editorial.editor", { storyId: s.id }, { llm: null });
    expect(r.displayName).toBe("Revisora Ana");
    expect(r.output!.agent_id).toBe("editorial.editor");
    const [c] = await sql()`select author_label from comments where story_id = ${s.id}`;
    expect(c!.author_label).toBe("Revisora Ana");
  });

  it("o contrato recusa saídas inválidas", () => {
    expect(validateOutput({ kind: "outra" }).ok).toBe(false);
    const fake = { schema_version: 1, agent_id: "editorial.research", run_id: "r", kind: "research_dossier", generated_at: "x",
      proposal: true, inputs: {}, sources_used: ["javascript:alert(1)"], cost: { calls: 0, input_tokens: 0, output_tokens: 0, usd_estimate: 0 },
      llm: { status: "skipped", model: "", reason: "" }, notes: [], story: { id: "s", version: 1, state: "idea" },
      pitch: { title: "t", angle: "", to_confirm: "" }, background: [], timeline: [], primary_sources: [], open_questions: [],
      interview_questions: [], summary: { text: "x", points: [{ text: "Disse algo", kind: "statement", attributed_to: "", evidence: [] }] } };
    const v = validateOutput(fake);
    expect(v.ok).toBe(false);
    if (!v.ok) expect(v.errors.join(" ")).toMatch(/endereço inválido.*declaração|declaração.*endereço inválido/s);
  });

  it("o cliente Gemini usa a API REST com a chave no cabeçalho e o modelo do ambiente", async () => {
    expect(llmFromEnv({})).toBeNull();
    const client = llmFromEnv({ GEMINI_API_KEY: "chave-teste" }) as GeminiClient;
    expect(client.model).toBe("gemini-2.5-flash-lite");
    expect((llmFromEnv({ GEMINI_API_KEY: "k", EDITORIAL_LLM_MODEL: "gemini-2.5-flash" }) as GeminiClient).model).toBe("gemini-2.5-flash");
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({
      candidates: [{ content: { parts: [{ text: '{"ok":true}' }] } }], usageMetadata: { promptTokenCount: 12, candidatesTokenCount: 3 } })));
    vi.stubGlobal("fetch", fetchMock);
    const res = await client.generate({ system: "s", prompt: "p", maxOutputTokens: 100 });
    expect(res).toEqual({ text: '{"ok":true}', inputTokens: 12, outputTokens: 3 });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent");
    expect((init.headers as Record<string, string>)["x-goog-api-key"]).toBe("chave-teste");
    expect(JSON.parse(init.body as string).generationConfig.maxOutputTokens).toBe(100);
  });
});
