/**
 * Investigação (`editorial.research`). Junta o que a redacção já tem sobre a peça (pauta, referências,
 * itens do radar relacionados) num dossier: contexto com endereços, cronologia, fontes primárias a consultar,
 * perguntas em aberto e perguntas de entrevista. Só usa endereços do material fornecido; as fontes primárias
 * sugeridas vêm de uma lista fixa e ficam marcadas «por consultar», nunca como factos.
 */
import type { Ctx } from "../context";
import { withCtx } from "../db";
import { similarity, titleKey } from "../text";
import { type BackgroundItem, check, type ClaimRecord, llmShapes, type PrimarySource, type ResearchDossier } from "./contracts";
import { llmJson, material } from "./llm";
import { type AgentOpts, type AgentResult, agentEnv, envelope, loadRefs, storyFor } from "./shared";
import { clip, fold, plain, termsRe } from "./textkit";

export const AGENT_ID = "editorial.research" as const;

interface SourceDef { label: string; url: string; why: string; terms: string[] }

/** Fontes institucionais portuguesas e europeias de dados primários (lista fixa, sem inventar endereços). */
export const PRIMARY_SOURCES: SourceDef[] = [
  { label: "INE — Instituto Nacional de Estatística", url: "https://www.ine.pt",
    why: "estatísticas oficiais (população, emprego, preços, habitação, censos)",
    terms: ["população", "emprego", "desemprego", "inflação", "preços", "habitação", "rendas", "censos", "salário", "salários", "pobreza", "estatística", "taxa", "natalidade", "turismo"] },
  { label: "PORDATA", url: "https://www.pordata.pt", why: "séries longas e comparação entre municípios e com a Europa",
    terms: ["município", "municípios", "concelho", "evolução", "série", "década", "região", "população", "envelhecimento"] },
  { label: "Diário da República", url: "https://diariodarepublica.pt", why: "texto oficial de leis, decretos, portarias, despachos e nomeações",
    terms: ["lei", "decreto", "decreto-lei", "portaria", "despacho", "regulamento", "nomeação", "nomeado", "nomeada", "governo", "ministério", "legislação"] },
  { label: "Portal BASE — contratos públicos", url: "https://www.base.gov.pt", why: "contratos públicos, ajustes directos e concursos",
    terms: ["contrato", "contratos", "ajuste direto", "ajuste directo", "concurso", "adjudicação", "adjudicou", "empreitada", "obra", "obras", "fornecedor", "câmara"] },
  { label: "Parlamento — Assembleia da República", url: "https://www.parlamento.pt", why: "iniciativas legislativas, votações, audições e perguntas ao Governo",
    terms: ["deputado", "deputada", "deputados", "parlamento", "assembleia", "proposta de lei", "projeto de lei", "projecto de lei", "votação", "partido", "orçamento"] },
  { label: "Eurostat", url: "https://ec.europa.eu/eurostat", why: "dados comparáveis entre países da União Europeia",
    terms: ["europa", "europeu", "europeia", "ue", "união europeia", "comparação", "países"] },
  { label: "Câmara municipal (actas, deliberações e contas; ver também o Portal Autárquico)", url: "https://portalautarquico.dgal.gov.pt",
    why: "deliberações, actas, orçamento e finanças do município",
    terms: ["câmara", "câmara municipal", "autarquia", "autarca", "presidente da câmara", "vereador", "vereadora", "junta", "freguesia", "município", "assembleia municipal"] },
  { label: "Universidades — repositórios científicos de acesso aberto (RCAAP)", url: "https://www.rcaap.pt",
    why: "estudos, teses e investigação revista por pares",
    terms: ["estudo", "estudos", "investigação", "investigador", "investigadora", "universidade", "científico", "científica", "especialista", "especialistas"] },
];
const DEFAULT_SOURCES = ["https://www.ine.pt", "https://www.pordata.pt", "https://diariodarepublica.pt"];
export const PRIMARY_SOURCE_URLS = new Set(PRIMARY_SOURCES.map((s) => s.url));

export function suggestPrimarySources(text: string): PrimarySource[] {
  const f = fold(text);
  const hits = PRIMARY_SOURCES.filter((s) => { const re = termsRe(s.terms); return re.test(f); });
  const chosen = hits.length ? hits : PRIMARY_SOURCES.filter((s) => DEFAULT_SOURCES.includes(s.url));
  return chosen.map((s) => ({ label: s.label, url: s.url, why: s.why, status: "por consultar" as const }));
}

interface FeedRow {
  id: string; url: string; title: string; title_key: string; excerpt: string; published_at: Date | null; topics: string[];
  story_id: string | null; source_name: string;
}

/** Perguntas de entrevista genéricas (propostas para a jornalista adaptar). */
function interviewQuestions(title: string, angle: string): string[] {
  const about = clip(angle.trim() || title, 120);
  return [
    `Que dados ou documentos sustentam o que está em causa em «${about}»?`,
    "Quem decidiu, quando e com que fundamento?",
    "Quem é directamente afectado e de que forma?",
    "O que muda a partir de agora, e em que prazos?",
    "Que alternativas foram consideradas e porque foram postas de lado?",
    "Quem discorda e com que argumentos?",
  ];
}

export async function buildDossier(ctx: Ctx, storyId: string, opts: AgentOpts = {}): Promise<AgentResult<ResearchDossier>> {
  const env = agentEnv(opts);
  const { story, refs, feed } = await withCtx(ctx, async (tx) => {
    const story = await storyFor(tx, ctx, storyId);
    const refs = await loadRefs(tx, storyId);
    const feed = await tx<FeedRow[]>`
      select fi.id, fi.url, fi.title, fi.title_key, fi.excerpt, fi.published_at, fi.topics, fi.story_id, fs.name as source_name
      from feed_items fi join feed_sources fs on fs.id = fi.feed_source_id
      where fi.status <> 'dismissed'
      order by coalesce(fi.published_at, fi.fetched_at) desc limit 500`;
    return { story, refs, feed };
  });

  // itens do radar: ligados à peça, com título semelhante, ou com tema em comum com as etiquetas
  const key = titleKey(`${story.title} ${story.angle}`);
  const tags = new Set(story.tags.map(fold));
  const related = feed
    .map((f) => {
      if (f.story_id === story.id) return { f, relation: "ligado à peça", score: 2 };
      const sim = similarity(key, f.title_key || titleKey(f.title));
      if (sim >= 0.25) return { f, relation: "título semelhante", score: 1 + sim };
      if (f.topics.some((t) => tags.has(fold(t)))) return { f, relation: "tema em comum", score: 0.5 };
      return null;
    })
    .filter((x): x is { f: FeedRow; relation: string; score: number } => x !== null)
    .sort((a, b) => b.score - a.score)
    .slice(0, 20);

  const background: BackgroundItem[] = [
    ...refs.map((r) => ({ title: r.title || r.url, url: r.url, source: r.credit, published_at: null,
      origin: "story_ref" as const, relation: `referência da peça (${r.kind})`, excerpt: clip(r.note, 300) })),
    ...related.map(({ f, relation }) => ({ title: f.title, url: f.url, source: f.source_name,
      published_at: f.published_at ? f.published_at.toISOString() : null, origin: "feed_item" as const, relation,
      excerpt: clip(f.excerpt, 300) })),
  ];
  const timeline = background
    .filter((b) => b.published_at)
    .sort((a, b) => a.published_at!.localeCompare(b.published_at!))
    .map((b) => ({ date: b.published_at!.slice(0, 10), title: b.title, url: b.url }));

  const text = [story.title, story.angle, story.to_confirm, story.subtitle, story.summary, plain(story.body), story.tags.join(" ")].join("\n");
  const primary = suggestPrimarySources(text);

  const open: string[] = story.to_confirm.split(/\n|;/).map((s) => s.trim()).filter(Boolean).map((s) => `Por confirmar: ${clip(s, 500)}`);
  if (!refs.some((r) => r.kind === "document" || r.kind === "data")) {
    open.push("Que documento ou conjunto de dados primário sustenta a peça? Ainda não há nenhum nas referências.");
  }
  if (/\d/.test(plain(story.body)) && refs.length === 0) open.push("Qual é a fonte de cada número citado no texto?");
  const outlets = new Set(related.filter((r) => r.relation !== "tema em comum").map((r) => r.f.source_name));
  if (outlets.size === 1) open.push("A notícia só aparece num meio: confirmar de forma independente antes de avançar.");
  if (outlets.size > 1) open.push(`O tema aparece em ${outlets.size} meios: a repetição não confirma nada; procurar a fonte original.`);
  if (!story.angle.trim()) open.push("Qual é o ângulo da peça? A pauta ainda não o define.");

  const questions = [...story.interview_questions.filter((q) => q.trim()), ...interviewQuestions(story.title, story.angle)]
    .map((q) => clip(q, 500)).slice(0, 15);

  // passo opcional: resumo SÓ do material fornecido, com cada ponto preso aos itens que o sustentam
  const items = background.map((b) => `${b.title} — ${b.excerpt} (${b.url})`);
  const urls = background.map((b) => b.url);
  let summary: ResearchDossier["summary"] = null;
  const step = items.length === 0
    ? { value: null, info: { status: "skipped" as const, model: env.llm?.model ?? "", reason: "sem material para resumir" } }
    : await llmJson<{ summary: string; points: { text: string; kind: ClaimRecord["kind"]; attributed_to: string; items: number[] }[] }>(env,
      [
        `Tarefa: resumir o contexto da pauta «${clip(story.title, 200)}» usando SÓ o material numerado.`,
        "Cada ponto indica em `items` os números do material que o sustentam. Um ponto sem material é \"unconfirmed\".",
        "Não escrevas endereços nem nomes que não estejam no material. Não inventes citações.",
        'Formato: {"summary":"...","points":[{"text":"...","kind":"fact|statement|inference|unconfirmed","attributed_to":"","items":[1]}]}',
        material(items),
      ].join("\n"),
      (v) => {
        const r = check<{ summary: string; points: { text: string; kind: ClaimRecord["kind"]; attributed_to: string; items: number[] }[] }>(llmShapes.summary, v);
        if (!r.ok) return r;
        const errs: string[] = [];
        const mentioned = [r.value.summary, ...r.value.points.map((p) => p.text)].join(" ").match(/https?:\/\/[^\s)»"]+/g) ?? [];
        if (mentioned.some((u) => !urls.includes(u.replace(/[.,;]$/, "")))) errs.push("endereço que não está no material");
        for (const p of r.value.points) {
          if (p.items.some((n) => !Number.isInteger(n) || n < 1 || n > items.length)) errs.push("ponto cita material inexistente");
          if (p.items.length === 0 && p.kind !== "unconfirmed") errs.push("ponto sem material tem de ser unconfirmed");
          if (p.kind === "statement" && !p.attributed_to.trim()) errs.push("declaração sem autor");
        }
        return errs.length ? { ok: false, errors: errs } : r;
      });
  if (step.value) {
    summary = {
      text: step.value.summary,
      points: step.value.points.map((p) => ({
        text: p.text, kind: p.kind, attributed_to: p.attributed_to,
        evidence: p.items.map((n) => ({ url: background[n - 1]!.url, title: background[n - 1]!.title, quote: "", relation: "cited" as const })),
      })),
    };
  }

  const output: ResearchDossier = {
    ...envelope<"research_dossier">(AGENT_ID, env,
      { story_id: story.id, story_version: story.version, refs: refs.map((r) => r.id), feed_items: related.map((r) => r.f.id) },
      urls, step.info, ["As fontes primárias sugeridas estão por consultar: não são factos nem foram lidas pelo agente."]),
    story: { id: story.id, version: story.version, state: story.state },
    pitch: { title: story.title, angle: story.angle, to_confirm: story.to_confirm },
    background,
    timeline,
    primary_sources: primary,
    open_questions: open.slice(0, 30),
    interview_questions: questions,
    summary,
  };
  const note = `Dossier de investigação: ${background.length} item(ns) de contexto, ${primary.length} fonte(s) primária(s) por consultar, `
    + `${open.length} pergunta(s) em aberto. Proposta para a jornalista usar ou rejeitar.`;
  return { output, note, llm: step.info };
}
