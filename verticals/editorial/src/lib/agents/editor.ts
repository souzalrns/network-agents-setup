/**
 * Edição assistida (`editorial.editor`). Lê a peça e propõe uma revisão: avisos de legibilidade, rigor e
 * atribuição, e rascunhos de adaptação a outros canais. NUNCA altera a peça: título, texto, citações e
 * factos ficam exactamente como estão; tudo é proposta para uma pessoa aceitar ou rejeitar.
 */
import type { Ctx } from "../context";
import { withCtx } from "../db";
import type { Story } from "../stories";
import {
  type ChannelAdaptations, check, type EditReview, type Finding, llmShapes, type Severity, type TextSuggestion,
} from "./contracts";
import { llmJson, material } from "./llm";
import { type AgentOpts, type AgentResult, agentEnv, type ClaimRow, envelope, LLM_SKIPPED, loadClaims, loadRefs, storyFor } from "./shared";
import {
  attributionSignals, clip, DATE_RE, fold, hasDocSource, hasSourceNearby, MONEY_RE, NUMBER_RE, PERCENT_RE, paragraphs, plain, quotes,
  sentences, termsRe, unconfirmedSignals, withoutQuotes, words,
} from "./textkit";

export const AGENT_ID = "editorial.editor" as const;

export const LIMITS = { title: 90, seoTitle: 60, metaDescription: 160, paragraphWords: 100, sentenceWords: 35 };

/** Palavras sensacionalistas ou carregadas. «polémica» só conta quando ninguém é citado na frase. */
export const LOADED_WORDS = ["chocante", "chocantes", "escândalo", "escândalos", "escandaloso", "escandalosa", "inacreditável",
  "inacreditáveis", "bomba", "bombástico", "bombástica", "caos", "vergonha", "vergonhoso", "vergonhosa", "incrível",
  "brutal", "assustador", "assustadora", "catástrofe", "catastrófico", "drama", "dramático", "dramática", "histórico",
  "polémica", "polémico"];
export const GENERALIZATIONS = ["toda a gente", "todos sabem", "sempre", "nunca", "ninguém", "jamais", "absolutamente", "completamente"];
export const VAGUE = ["alguns especialistas", "vários especialistas", "muitos especialistas", "vários estudos", "estudos mostram",
  "muitas pessoas", "há quem diga", "há quem defenda", "fontes próximas", "segundo se sabe", "de alguma forma",
  "em certa medida", "cada vez mais", "de certa forma", "um grande número", "inúmeros"];

const reLoaded = termsRe(LOADED_WORDS);
const reGeneral = termsRe(GENERALIZATIONS);
const reVague = termsRe(VAGUE);
const PASSIVE = /\b(?:foi|foram|é|são|será|serão|era|eram|seja|sejam|fosse|fossem|tem sido|têm sido|tinha sido|tinham sido)\s+(?:\p{L}+mente\s+)?\p{L}+(?:ado|ada|ados|adas|ido|ida|idos|idas)\b/iu;

const finding = (severity: Severity, rule: string, field: Finding["field"], excerpt: string, suggestion: string): Finding =>
  ({ severity, rule, field, excerpt: clip(excerpt, 300), suggestion });

/** Verificações determinísticas. Função pura: recebe a peça e as afirmações, devolve avisos. */
export function reviewText(story: Pick<Story, "title" | "subtitle" | "summary" | "body" | "seo_title" | "meta_description">,
  claims: Pick<ClaimRow, "text" | "kind" | "verification" | "in_article">[] = []): Finding[] {
  const out: Finding[] = [];
  const title = story.title.trim();

  // --- campos e tamanhos
  if (title.length > LIMITS.title) {
    out.push(finding("warning", "title.length", "title", title,
      `O título tem ${title.length} caracteres (máximo recomendado ${LIMITS.title}). Propor uma versão mais curta, sem perder o essencial.`));
  }
  if (!story.summary.trim()) out.push(finding("warning", "summary.missing", "summary", "", "Falta o resumo (lead curto que aparece nas listagens e partilhas)."));
  if (!story.subtitle.trim()) out.push(finding("info", "subtitle.missing", "subtitle", "", "Sem subtítulo: considerar um que complete o título."));
  if (!story.seo_title.trim()) out.push(finding("info", "seo.title_missing", "seo_title", "", "Sem título para motores de busca (usa-se o título da peça)."));
  else if (story.seo_title.length > LIMITS.seoTitle) {
    out.push(finding("info", "seo.title_length", "seo_title", story.seo_title, `Título SEO com ${story.seo_title.length} caracteres (recomendado até ${LIMITS.seoTitle}).`));
  }
  if (!story.meta_description.trim()) out.push(finding("info", "seo.description_missing", "meta_description", "", "Sem descrição para motores de busca e partilhas."));
  else if (story.meta_description.length > LIMITS.metaDescription) {
    out.push(finding("info", "seo.description_length", "meta_description", story.meta_description,
      `Descrição com ${story.meta_description.length} caracteres (recomendado até ${LIMITS.metaDescription}).`));
  }
  const body = plain(story.body);
  if (!body.trim()) out.push(finding("warning", "body.empty", "body", "", "A peça ainda não tem texto."));

  // --- legibilidade
  const paras = paragraphs(body);
  for (const p of paras) {
    const n = words(p).length;
    if (n > LIMITS.paragraphWords) {
      out.push(finding("warning", "readability.long_paragraph", "body", p,
        `Parágrafo com ${n} palavras (recomendado até ${LIMITS.paragraphWords}). Propor dividir numa ideia por parágrafo.`));
    }
  }
  const allSentences = paras.flatMap((p) => sentences(p));
  for (const s of allSentences) {
    const n = words(s).length;
    if (n > LIMITS.sentenceWords) {
      out.push(finding("info", "readability.long_sentence", "body", s, `Frase com ${n} palavras: propor dividir em duas.`));
    }
  }
  const passive = allSentences.filter((s) => PASSIVE.test(s));
  if (passive.length >= 3 && passive.length / Math.max(allSentences.length, 1) >= 0.3) {
    out.push(finding("info", "wording.passive", "body", passive[0]!,
      `${passive.length} de ${allSentences.length} frases na voz passiva: preferir dizer quem fez o quê.`));
  }

  // --- linguagem carregada, generalizações, vaguezas (título, subtítulo, resumo e texto)
  const fields: [Finding["field"], string][] = [["title", title], ["subtitle", story.subtitle], ["summary", story.summary], ["body", body]];
  for (const [field, text] of fields) {
    for (const s of sentences(text)) {
      const f = fold(withoutQuotes(s)); // o que está entre aspas é de quem é citado
      const attributed = attributionSignals(s).length > 0;
      for (const m of f.matchAll(reLoaded)) {
        const w = m[1]!;
        if ((w === "polemica" || w === "polemico") && attributed) continue;
        out.push(finding("warning", "wording.loaded", field, s,
          `Palavra carregada («${w}»): descrever o facto e deixar o leitor avaliar, ou atribuir a qualificação a quem a fez.`));
      }
      for (const m of f.matchAll(reGeneral)) {
        if (attributed) continue;
        out.push(finding("info", "wording.generalization", field, s, `Generalização («${m[1]}»): confirmar se é literalmente verdade ou concretizar.`));
      }
      for (const m of f.matchAll(reVague)) {
        out.push(finding("warning", "wording.vague", field, s, `Expressão vaga («${m[1]}»): dizer quem, quantos, que estudo ou que fonte.`));
      }
      const unconf = unconfirmedSignals(s);
      if (unconf.length) {
        out.push(finding("warning", "wording.unconfirmed", field, s,
          `Marca de informação não confirmada («${unconf[0]}»): confirmar com fonte identificada ou retirar do texto antes de aprovar.`));
      }
    }
  }

  // --- citações sem atribuição por perto (a frase, a anterior e a seguinte)
  for (const [field, text] of fields) {
    const ss = sentences(text);
    ss.forEach((s, i) => {
      for (const q of quotes(s)) {
        if (words(q.text).length < 4) continue; // termo entre aspas, não uma citação
        const near = [ss[i - 1] ?? "", s].join(" "); // a atribuição vem na própria frase ou a introduz («O ministro explicou: …»)
        if (attributionSignals(near).length === 0) {
          out.push(finding("warning", "quote.unattributed", field, s,
            "Citação sem indicação de quem a disse por perto: identificar o autor (nome e função) ou retirar as aspas."));
        }
      }
    });
  }

  // --- números, percentagens, valores e datas sem fonte por perto (no resumo e no texto; um título não cita fontes)
  for (const [field, text] of fields.filter(([f]) => f === "summary" || f === "body")) {
    const ss = sentences(text);
    ss.forEach((s, i) => {
      const hasPct = new RegExp(PERCENT_RE.source, "giu").test(s);
      const hasMoney = new RegExp(MONEY_RE.source, "giu").test(s);
      const stripped = s.replace(new RegExp(DATE_RE.source, "giu"), " ");
      const hasNumber = new RegExp(NUMBER_RE.source, "g").test(stripped);
      const hasDate = new RegExp(DATE_RE.source, "giu").test(s);
      if (!hasPct && !hasMoney && !hasNumber && !hasDate) return;
      if (hasSourceNearby(s) || hasDocSource(ss[i - 1] ?? "")) return;
      const what = hasPct ? "percentagem" : hasMoney ? "valor" : hasNumber ? "número" : "data";
      out.push(finding(what === "data" ? "info" : "warning", "number.unsourced", field, s,
        `${what[0]!.toUpperCase()}${what.slice(1)} sem fonte indicada por perto: dizer de onde vem (documento, entidade, estudo).`));
    });
  }

  // --- afirmações registadas
  for (const c of claims) {
    if (!c.in_article) continue;
    if (c.kind === "unconfirmed") {
      out.push(finding("blocker", "claim.unconfirmed_in_article", "claims", c.text,
        "Informação não confirmada marcada como estando no artigo: confirmar e reclassificar, ou retirar do texto. Impede a aprovação."));
    } else if (c.kind === "fact" && c.verification !== "verified") {
      out.push(finding("blocker", "claim.fact_unverified", "claims", c.text,
        "Facto ainda não verificado por uma pessoa: juntar evidência e verificar, ou retirar do artigo. Impede a aprovação."));
    } else if (c.verification === "disputed" || c.verification === "unsupported") {
      out.push(finding("warning", "claim.disputed", "claims", c.text, "Afirmação contestada ou sem suporte ainda no artigo."));
    }
  }
  return out;
}

/** Rascunhos de adaptação a outros canais. Usa frases inteiras do texto, sem as alterar nem cortar citações. */
export function adaptations(story: Pick<Story, "title" | "subtitle" | "summary" | "body">, refUrls: string[]): ChannelAdaptations {
  const usable = paragraphs(plain(story.body))
    .map((p) => sentences(p)[0] ?? "")
    .filter((s) => s && unconfirmedSignals(s).length === 0 && (s.length <= 220 || quotes(s).length === 0));
  const short = (s: string, max: number) => (s.length <= max ? s : clip(s, max));
  const lead = story.summary.trim() || story.subtitle.trim() || usable[0] || story.title;
  const keys = usable.filter((s) => s !== lead).slice(0, 3).map((s) => short(s, 220));

  const slides = [story.title, lead, ...keys, "Lê a peça completa (ligação na biografia)."]
    .map((text, i) => ({ n: i + 1, text: short(text, 380) }));
  const beats = [
    { from_s: 0, to_s: 5, text: `Gancho: ${short(story.title, 200)}` },
    { from_s: 5, to_s: 20, text: `Contexto: ${short(lead, 400)}` },
    { from_s: 20, to_s: 45, text: `Pontos principais: ${keys.length ? keys.map((k) => short(k, 160)).join(" / ") : "(a definir pela redacção)"}` },
    { from_s: 45, to_s: 55, text: "Fecho: onde ler a peça completa e convite a comentar." },
  ];
  const yt = [story.title, "", lead, "",
    ...(refUrls.length ? ["Referências:", ...refUrls.slice(0, 10).map((u) => `- ${u}`), ""] : []),
    "[Rascunho gerado automaticamente: rever antes de publicar]"].join("\n");
  return {
    draft: true,
    label: "Rascunhos para revisão humana: não publicar sem aprovação da edição.",
    instagram_carousel: { slides },
    reel_script: { target_seconds: { min: 45, max: 60 }, beats },
    youtube_description: { text: yt.slice(0, 4900) },
    podcast_points: { points: [lead, ...keys].map((p) => short(p, 500)).slice(0, 8) },
  };
}

const countBy = (f: Finding[]) => ({
  info: f.filter((x) => x.severity === "info").length,
  warning: f.filter((x) => x.severity === "warning").length,
  blocker: f.filter((x) => x.severity === "blocker").length,
});

/** Revisão da peça. Só lê a peça; não lhe toca. */
export async function reviewArticle(ctx: Ctx, storyId: string, opts: AgentOpts = {}): Promise<AgentResult<EditReview>> {
  const env = agentEnv(opts);
  const { story, claims, refs } = await withCtx(ctx, async (tx) => {
    const story = await storyFor(tx, ctx, storyId);
    return { story, claims: await loadClaims(tx, storyId), refs: await loadRefs(tx, storyId) };
  });
  const findings = reviewText(story, claims);
  const refUrls = refs.map((r) => r.url);

  // passo opcional: sugestões de texto, cada uma presa a um excerto literal da peça
  let suggestions: TextSuggestion[] = [];
  let llm = LLM_SKIPPED;
  const fullText = [story.title, story.subtitle, story.summary, plain(story.body)].join("\n");
  const norm = (s: string) => s.replace(/\s+/g, " ").trim();
  const step = await llmJson<{ suggestions: { rule: string; excerpt: string; suggestion: string }[] }>(env,
    [
      "Tarefa: rever a legibilidade e o rigor da peça abaixo. Devolve no máximo 8 sugestões de reescrita.",
      "Cada sugestão tem `excerpt` (cópia LITERAL de um trecho da peça), `rule` (curta) e `suggestion` (proposta).",
      "Não mudes factos, números, nomes nem citações; não proponhas texto novo com informação que não esteja na peça.",
      'Formato: {"suggestions":[{"rule":"...","excerpt":"...","suggestion":"..."}]}',
      material([`Título: ${story.title}`, `Subtítulo: ${story.subtitle}`, `Resumo: ${story.summary}`, `Texto:\n${plain(story.body).slice(0, 12_000)}`]),
    ].join("\n"),
    (v) => {
      const r = check<{ suggestions: { rule: string; excerpt: string; suggestion: string }[] }>(llmShapes.editSuggestions, v);
      if (!r.ok) return r;
      const bad = r.value.suggestions.filter((s) => !norm(fullText).includes(norm(s.excerpt)));
      return bad.length ? { ok: false, errors: [`${bad.length} sugestão(ões) com excerto que não existe na peça`] } : r;
    });
  llm = step.info;
  if (step.value) suggestions = step.value.suggestions.map((s) => ({ ...s, origin: "llm" as const }));

  const output: EditReview = {
    ...envelope<"edit_review">(AGENT_ID, env, { story_id: story.id, story_version: story.version, claims: claims.length, refs: refs.length },
      refUrls, llm, ["A peça não foi alterada: avisos e rascunhos são propostas."]),
    story: { id: story.id, version: story.version, state: story.state },
    findings,
    counts: countBy(findings),
    adaptations: adaptations(story, refUrls),
    suggestions,
  };
  const c = output.counts;
  const note = `Revisão automática (versão ${story.version}): ${c.blocker} bloqueio(s), ${c.warning} aviso(s), ${c.info} nota(s). `
    + "Proposta para a edição aceitar ou rejeitar; o texto não foi alterado.";
  return { output, note, llm };
}
