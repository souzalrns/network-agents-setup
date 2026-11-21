import Link from "next/link";
import { notFound } from "next/navigation";
import { Empty, Flash, SectionTag, StatePill } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import {
  CHANNEL_LABEL, CLAIM_KIND_HELP, CLAIM_KIND_LABEL, CONF_LABEL, DIST_STATE_LABEL, FORMATS, OUTPUT_KIND_LABEL, USAGE_LABEL, VERIFICATION_LABEL,
} from "@/lib/constants";
import { canWrite, isDesk } from "@/lib/context";
import { withCtx } from "@/lib/db";
import { articleOf, getDraft } from "@/lib/drafts";
import { fmtDateTime, relTime, toLocalInput } from "@/lib/format";
import { agentName, getPublication } from "@/lib/publication";
import { listSections, listSources, listTeam, storyDetail } from "@/lib/queries";
import { isOwner, nextSteps, STATE_LABEL } from "@/lib/workflow";
import {
  addClaimAction, addCorrectionAction, addRefAction, commentAction, distributionStateAction, linkSourceAction, removeRefAction,
  resolveCommentAction, reviewOutputAction, saveDistributionAction, saveSourceAction, transitionAction, unlinkSourceAction,
  updateArticleAction, updateClaimAction, updatePitchAction, verifyClaimAction,
} from "../../../actions";
import { AgentPanel } from "./agent-panel";
import { ArticleEditor } from "./article-editor";

type SP = Record<string, string | string[] | undefined>;

export default async function StoryPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<SP> }) {
  const { id } = await params;
  const sp = await searchParams;
  const { user, ctx } = await requireUser();
  if (!/^[0-9a-f-]{36}$/i.test(id)) notFound();
  const d = await storyDetail(ctx, id);
  if (!d) notFound();
  const [pub, sections, team, allSources, draft] = await Promise.all([
    getPublication(ctx),
    withCtx(ctx, (tx) => listSections(tx)),
    withCtx(ctx, (tx) => listTeam(tx)),
    listSources(ctx),
    withCtx(ctx, (tx) => getDraft(tx, id)),
  ]);
  const s = d.story;
  const actors = { assigneeId: s.assignee_id, authorId: s.author_id, createdBy: s.created_by };
  const steps = nextSteps(s.state, user.role, user.userId, actors);
  const editable = canWrite(user.role) && (isDesk(user.role) || isOwner(user.userId, actors))
    && (!["approved", "scheduled", "published"].includes(s.state) || isDesk(user.role)) && s.state !== "archived";
  const section = sections.find((x) => x.id === s.section_id);
  const nameOf = (uid: string | null) => team.find((m) => m.user_id === uid)?.name ?? null;
  const fourEyes = pub.settings?.require_second_reviewer !== false;
  // a mesma regra da base de dados (story_claims_block): não confirmadas, factos por verificar e tudo o que foi contestado
  const blockers = d.claims.filter((c) => c.in_article && (c.kind === "unconfirmed" || (c.kind === "fact" && c.verification !== "verified")
    || ["disputed", "unsupported"].includes(c.verification)));
  const linked = new Set(d.sources.map((x) => x.id));
  const showArticle = !["idea", "pitch_proposed"].includes(s.state) || s.body.length > 0;

  return (
    <>
      <div className="nr-head">
        <div style={{ minWidth: 0 }}>
          <p className="label"><Link href="/redacao/pautas">Pautas e peças</Link> · {s.format}</p>
          <h1 style={{ overflowWrap: "anywhere" }}>{s.title}</h1>
          <div className="meta" style={{ marginTop: 6 }}>
            <StatePill state={s.state} />
            <SectionTag name={section?.name ?? null} color={section?.color ?? null} />
            <span>Responsável: {nameOf(s.assignee_id) ?? "por atribuir"}</span>
            {s.author_id && <span>Autoria: {nameOf(s.author_id)}</span>}
            <span>Versão {s.version}</span>
            {s.origin !== "human" && <span>Ideia sugerida pelo {s.origin === "radar" ? "radar" : "agente"}</span>}
            {s.state === "published" && s.slug && <a href={`/artigo/${s.slug}`} target="_blank" rel="noreferrer">Ver no site</a>}
          </div>
        </div>
      </div>
      <Flash sp={sp} />
      {steps.length > 0 && <a className="btn jump show-md" href="#passo">Próximo passo: {steps.map((x) => x.label).slice(0, 2).join(" · ")}{steps.length > 2 ? "…" : ""} ↓</a>}

      <div className="story-layout">
        <div className="stack">
          <nav className="tabs" aria-label="Secções da peça">
            <a href="#pauta">Pauta</a>{showArticle && <a href="#artigo">Artigo</a>}<a href="#verificacao">Verificação</a>
            <a href="#referencias">Referências</a><a href="#fontes">Fontes</a><a href="#comentarios">Comentários</a>
            <a href="#agentes">Agentes</a>{["approved", "scheduled", "published"].includes(s.state) && <a href="#distribuicao">Distribuição</a>}
          </nav>

          <section className="card" id="pauta">
            <h2>Pauta</h2>
            <form action={updatePitchAction} className="stack">
              <input type="hidden" name="id" value={s.id} />
              <fieldset disabled={!editable} style={{ border: 0, padding: 0, margin: 0 }} className="stack">
                <label className="field"><span>Título de trabalho</span><input id="p-title" name="title" defaultValue={s.title} required maxLength={300} /></label>
                <div className="grid2">
                  <label className="field"><span>Editoria</span>
                    <select id="p-section" name="section_id" defaultValue={s.section_id ?? ""}><option value="">Por definir</option>{sections.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
                  <label className="field"><span>Formato</span>
                    <select id="p-format" name="format" defaultValue={s.format}>{[...new Set([s.format, ...FORMATS])].map((f) => <option key={f}>{f}</option>)}</select></label>
                  <label className="field"><span>Prioridade</span>
                    <select id="p-priority" name="priority" defaultValue={String(s.priority)}><option value="1">Alta</option><option value="2">Normal</option><option value="3">Baixa</option></select></label>
                  <label className="field"><span>Prazo</span><input id="p-due" type="date" name="due_date" defaultValue={s.due_date ?? ""} /></label>
                  {isDesk(user.role) && (
                    <label className="field"><span>Responsável</span>
                      <select id="p-assignee" name="assignee_id" defaultValue={s.assignee_id ?? ""}><option value="">Por atribuir</option>
                        {team.filter((m) => m.role !== "reviewer").map((m) => <option key={m.user_id} value={m.user_id}>{m.name}</option>)}</select></label>
                  )}
                </div>
                <label className="field"><span>Ângulo de investigação</span><textarea id="p-angle" name="angle" defaultValue={s.angle} /></label>
                <label className="field"><span>A confirmar antes de avançar</span><textarea id="p-confirm" name="to_confirm" defaultValue={s.to_confirm} /></label>
                <label className="field"><span>Perguntas para entrevista</span><textarea id="p-questions" name="interview_questions" defaultValue={s.interview_questions.join("\n")} /><small>Uma por linha.</small></label>
                {editable && s.state === "published" && (
                  <label className="field"><span>Nota da alteração (obrigatória numa peça publicada)</span>
                    <input id="p-note" name="note" required maxLength={300} placeholder="Ex.: mudou de editoria" /></label>
                )}
                {editable && <div><button className="btn" type="submit">Guardar pauta</button></div>}
              </fieldset>
            </form>
          </section>

          {showArticle && (
            <section className="card" id="artigo">
              <h2>Artigo <span className="label">versão {s.version}</span></h2>
              {editable && ["approved", "scheduled"].includes(s.state) && <p className="muted" style={{ marginTop: 0 }}>Guardar alterações a esta peça retira a aprovação: volta a «em revisão».</p>}
              {!editable && ["approved", "scheduled", "published"].includes(s.state) && <p className="muted" style={{ marginTop: 0 }}>Peça aprovada: só a edição altera o texto (e alterar retira a aprovação).</p>}
              {s.state === "archived" && <p className="muted" style={{ marginTop: 0 }}>Peça arquivada: para a alterar, reabre-a como ideia.</p>}
              <ArticleEditor key={`${s.version}-${draft?.rev ?? 0}-${draft?.updated_by ?? ""}`} storyId={s.id} version={s.version} state={s.state} editable={editable} me={user.userId} action={updateArticleAction}
                saved={articleOf(s)} draft={draft ? { ...draft, updated_at: draft.updated_at.toISOString(), lease_until: draft.lease_until?.toISOString() ?? null } : null}
                photos={d.refs.filter((r) => r.kind === "photo").map((r) => ({ url: r.url, title: r.title, credit: r.credit }))} />
              <p className="meta" style={{ marginTop: 10 }}><Link href={`/redacao/pecas/${s.id}/versoes`}>Histórico de versões, comparação e restauro</Link></p>
            </section>
          )}

          <section className="card" id="verificacao">
            <h2>Verificação <span className="label">{d.claims.length} afirmações</span></h2>
            {blockers.length > 0 && <p className="flash erro" style={{ marginTop: 0 }}>{blockers.length} {blockers.length === 1 ? "afirmação impede" : "afirmações impedem"} a aprovação: factos por verificar, informação não confirmada ou afirmações contestadas no artigo.</p>}
            <div className="list">{d.claims.length ? d.claims.map((c) => {
              const own = fourEyes && (c.created_by === user.userId || s.author_id === user.userId);
              const canVerify = (canWrite(user.role) || user.role === "reviewer") && !own;
              return (
              <div key={c.id} className="stack claim" style={{ gap: 6 }}>
                <div><b>{CLAIM_KIND_LABEL[c.kind]}</b>{c.attributed_to && <> · {c.attributed_to}</>} {c.origin === "agent" && <span className="label">proposta pelo agente</span>}
                  {" "}<span className={`pill v-${c.verification}`}>{VERIFICATION_LABEL[c.verification]}</span>{!c.in_article && <span className="label"> fora do artigo</span>}</div>
                <div style={{ overflowWrap: "anywhere" }}>{c.text}</div>
                {c.evidence.length > 0 && <div className="meta">Evidência: {c.evidence.map((e, i) => <a key={i} href={e.url} target="_blank" rel="noreferrer">{e.title || e.url}</a>)}</div>}
                {c.verification === "verified" && <div className="meta">Verificada por {c.verified_name}</div>}
                {canWrite(user.role) && (
                  <form action={updateClaimAction} className="row">
                    <input type="hidden" name="id" value={s.id} /><input type="hidden" name="claim" value={c.id} />
                    <label className="check"><input type="checkbox" name="in_article" value="1" defaultChecked={c.in_article} /> No artigo</label>
                    <input name="evidence_url" type="url" placeholder="Acrescentar evidência (https://…)" style={{ flex: "1 1 200px", width: "auto" }} aria-label="Evidência" />
                    <button className="btn small" type="submit">Guardar</button>
                  </form>
                )}
                {canVerify ? (
                  <form action={verifyClaimAction} className="row">
                    <input type="hidden" name="id" value={s.id} /><input type="hidden" name="claim" value={c.id} />
                    <select name="verification" defaultValue={c.verification} aria-label="Estado da verificação" style={{ width: "auto" }}>
                      {Object.entries(VERIFICATION_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
                    <button className="btn small primary" type="submit">Registar verificação</button>
                  </form>
                ) : own && <p className="meta" style={{ margin: 0 }}>Escreveste a peça ou registaste a afirmação: a verificação é de outra pessoa.</p>}
              </div>); }) : <Empty>Ainda não há afirmações registadas. Regista os números, datas e citações que o artigo usa.</Empty>}</div>
            {canWrite(user.role) && (
              <details className="box" style={{ marginTop: 12 }}><summary>Registar afirmação</summary>
                <form action={addClaimAction} className="stack" style={{ marginTop: 10 }}>
                  <input type="hidden" name="id" value={s.id} />
                  <label className="field"><span>Afirmação</span><textarea id="c-text" name="text" required style={{ minHeight: 60 }} /></label>
                  <div className="grid2">
                    <label className="field"><span>Tipo</span><select id="c-kind" name="kind" defaultValue="fact">
                      {Object.entries(CLAIM_KIND_LABEL).map(([k, v]) => <option key={k} value={k}>{v} — {CLAIM_KIND_HELP[k]}</option>)}</select></label>
                    <label className="field"><span>Quem declarou (declarações)</span><input id="c-attr" name="attributed_to" /></label>
                    <label className="field"><span>Evidência</span><input id="c-ev" name="evidence_url" type="url" placeholder="https://…" /></label>
                    <label className="field"><span>Título da evidência</span><input id="c-evt" name="evidence_title" /></label>
                  </div>
                  <div><button className="btn" type="submit">Registar</button></div>
                </form>
              </details>
            )}
          </section>

          <section className="card" id="referencias">
            <h2>Referências e anexos <span className="label">{d.refs.length}</span></h2>
            <div className="list">{d.refs.length ? d.refs.map((r) => (
              <div key={r.id} className="row" style={{ justifyContent: "space-between" }}>
                <div style={{ minWidth: 0 }}><a className="item-title" href={r.url} target="_blank" rel="noreferrer">{r.title || r.url}</a>
                  <div className="meta"><span>{r.kind}</span>{r.credit && <span>{r.credit}</span>}{r.added_kind === "agent" && <span>proposta pelo agente</span>}{r.note && <span>{r.note}</span>}</div></div>
                {canWrite(user.role) && <form action={removeRefAction}><input type="hidden" name="id" value={s.id} /><input type="hidden" name="ref" value={r.id} /><button className="btn small danger" type="submit">Retirar</button></form>}
              </div>)) : <Empty>Documentos, dados, fotografias, vídeos ou áudios que sustentam a peça.</Empty>}</div>
            {canWrite(user.role) && (
              <form action={addRefAction} className="row" style={{ marginTop: 12 }}>
                <input type="hidden" name="id" value={s.id} />
                <input name="url" type="url" required placeholder="https://…" aria-label="Endereço" style={{ flex: "2 1 220px", width: "auto" }} />
                <input name="title" placeholder="Título" aria-label="Título" style={{ flex: "1 1 160px", width: "auto" }} />
                <select name="kind" aria-label="Tipo" style={{ width: "auto" }}><option value="document">Documento</option><option value="data">Dados</option><option value="article">Artigo</option><option value="photo">Fotografia</option><option value="video">Vídeo</option><option value="audio">Áudio</option></select>
                <input name="credit" placeholder="Crédito" aria-label="Crédito" style={{ flex: "1 1 120px", width: "auto" }} />
                <button className="btn" type="submit">Acrescentar</button>
              </form>
            )}
          </section>

          <section className="card" id="fontes">
            <h2>Fontes <span className="label">protegidas: nunca visíveis para agentes ou público</span></h2>
            <div className="list">{d.sources.length ? d.sources.map((x) => (
              <div key={x.id} className="row" style={{ justifyContent: "space-between" }}>
                <div><b>{x.name}</b>{x.organization && <> · {x.organization}</>}
                  <div className="meta"><span>{USAGE_LABEL[x.usage]}</span><span>{CONF_LABEL[x.confidentiality]}</span>{x.contact && <span>{x.contact}</span>}</div></div>
                {canWrite(user.role) && <form action={unlinkSourceAction}><input type="hidden" name="id" value={s.id} /><input type="hidden" name="source" value={x.id} /><button className="btn small" type="submit">Retirar</button></form>}
              </div>)) : <Empty>Nenhuma fonte associada.</Empty>}</div>
            {canWrite(user.role) && (
              <div className="stack" style={{ marginTop: 12 }}>
                {allSources.filter((x) => !linked.has(x.id)).length > 0 && (
                  <form action={linkSourceAction} className="row">
                    <input type="hidden" name="id" value={s.id} />
                    <select name="source" aria-label="Fonte" style={{ flex: "2 1 220px", width: "auto" }}>
                      {allSources.filter((x) => !linked.has(x.id)).map((x) => <option key={x.id} value={x.id}>{x.name}{x.organization ? ` · ${x.organization}` : ""}</option>)}</select>
                    <select name="usage" aria-label="Uso" style={{ width: "auto" }}>{Object.entries(USAGE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
                    <button className="btn" type="submit">Associar</button>
                  </form>
                )}
                <details className="box"><summary>Nova fonte</summary>
                  <form action={saveSourceAction} className="stack" style={{ marginTop: 10 }}>
                    <input type="hidden" name="story" value={s.id} /><input type="hidden" name="back" value={`/redacao/pecas/${s.id}#fontes`} />
                    <div className="grid2">
                      <label className="field"><span>Nome</span><input id="f-name" name="name" required /></label>
                      <label className="field"><span>Organização</span><input id="f-org" name="organization" /></label>
                      <label className="field"><span>Contacto</span><input id="f-contact" name="contact" /></label>
                      <label className="field"><span>Confidencialidade</span><select id="f-conf" name="confidentiality" defaultValue="internal">{Object.entries(CONF_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
                      <label className="field"><span>Uso nesta peça</span><select id="f-usage" name="usage">{Object.entries(USAGE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
                    </div>
                    <div><button className="btn" type="submit">Guardar fonte</button></div>
                  </form>
                </details>
              </div>
            )}
          </section>

          <section className="card" id="comentarios">
            <h2>Comentários e revisão <span className="label">{d.comments.filter((c) => !c.resolved_at).length} por resolver</span></h2>
            <div className="list">{d.comments.length ? d.comments.map((c) => (
              <div key={c.id} style={{ opacity: c.resolved_at ? 0.6 : 1 }}>
                <div className="meta"><b style={{ color: "var(--ink)" }}>{c.name ?? c.author_label ?? "Agente"}</b>
                  {c.kind === "review" && <span className="pill" style={{ "--c": "var(--s-review)" } as React.CSSProperties}>Revisão</span>}
                  {c.kind === "agent_note" && <span className="label">nota de agente</span>}<span>{relTime(c.created_at)}</span>
                  {c.resolved_at ? <span>resolvido</span> : <form action={resolveCommentAction}><input type="hidden" name="id" value={s.id} /><input type="hidden" name="comment" value={c.id} /><button className="btn link" type="submit">Marcar como resolvido</button></form>}</div>
                <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{c.body}</div>
              </div>)) : <Empty>Sem comentários.</Empty>}</div>
            <form action={commentAction} className="stack" style={{ marginTop: 12 }}>
              <input type="hidden" name="id" value={s.id} />
              <label className="field"><span className="sr-only">Comentário</span><textarea id="k-body" name="body" placeholder="Escreve um comentário para a equipa" style={{ minHeight: 70 }} /></label>
              <div className="row"><button className="btn" type="submit">Comentar</button>
                <label className="check"><input type="checkbox" name="review" value="1" /> É um pedido de revisão</label></div>
            </form>
          </section>

          <section className="card" id="agentes">
            <h2>Agentes <span className="label">propostas, nunca decisões</span></h2>
            <AgentPanel storyId={s.id} canRun={canWrite(user.role)} names={{
              research: agentName(pub, "editorial.research"), factcheck: agentName(pub, "editorial.factcheck"), editor: agentName(pub, "editorial.editor"),
            }} />
            <div className="list" style={{ marginTop: 12 }}>{d.outputs.length ? d.outputs.map((o) => (
              <details key={o.id} className="box" open={o.status === "proposed" && d.outputs[0]?.id === o.id}>
                <summary>{agentName(pub, o.agent_id)} · {OUTPUT_KIND_LABEL[o.kind] ?? o.kind} · {relTime(o.created_at)} · {o.status === "proposed" ? "por rever" : o.status === "accepted" ? "aproveitada" : "descartada"}</summary>
                <OutputView payload={o.payload} />
                {o.status === "proposed" && canWrite(user.role) && (
                  <div className="row" style={{ marginTop: 10 }}>
                    {(["accepted", "dismissed"] as const).map((st) => (
                      <form key={st} action={reviewOutputAction}><input type="hidden" name="output" value={o.id} /><input type="hidden" name="status" value={st} />
                        <input type="hidden" name="back" value={`/redacao/pecas/${s.id}#agentes`} />
                        <button className="btn small" type="submit">{st === "accepted" ? "Aproveitar" : "Descartar"}</button></form>))}
                  </div>
                )}
              </details>)) : <Empty>Nenhum agente trabalhou nesta peça ainda.</Empty>}</div>
          </section>

          {["approved", "scheduled", "published"].includes(s.state) && (
            <section className="card" id="distribuicao">
              <h2>Distribuição <span className="label">só segue para o agendador depois de aprovada</span></h2>
              <div className="list">{d.distribution.length ? d.distribution.map((x) => (
                <div key={x.id} className="stack" style={{ gap: 6 }}>
                  <div className="meta"><b style={{ color: "var(--ink)" }}>{CHANNEL_LABEL[x.channel]}</b><span>{DIST_STATE_LABEL[x.state]}</span>{x.prepared_label && <span>preparado por {x.prepared_label}</span>}</div>
                  <form action={saveDistributionAction} className="stack" style={{ gap: 6 }}>
                    <input type="hidden" name="id" value={s.id} /><input type="hidden" name="item" value={x.id} /><input type="hidden" name="channel" value={x.channel} />
                    <textarea name="text" defaultValue={String(x.content.text ?? "")} aria-label="Texto" style={{ minHeight: 80 }} />
                    <input name="link" defaultValue={String(x.content.link ?? "")} placeholder="Ligação" aria-label="Ligação" />
                    <input name="media_url" defaultValue={String(x.content.media_url ?? "")} placeholder="Imagem ou vídeo (https://…)" aria-label="Media" />
                    <div><button className="btn small" type="submit">Guardar texto</button></div>
                  </form>
                  <div className="row">
                    {([
                      ["approved", "Aprovar", isDesk(user.role) && x.state !== "approved" && x.state !== "handed_off", "primary"],
                      ["in_review", "Pedir revisão", x.state === "draft", ""],
                      ["discarded", "Descartar", isDesk(user.role) && !["handed_off", "published"].includes(x.state), "danger"],
                    ] as const).filter(([, , show]) => show).map(([st, label, , cls]) => (
                      <form key={st} action={distributionStateAction}>
                        <input type="hidden" name="id" value={s.id} /><input type="hidden" name="item" value={x.id} />
                        <input type="hidden" name="state" value={st} />
                        <button className={`btn small ${cls}`} type="submit">{label}</button>
                      </form>
                    ))}
                  </div>
                </div>)) : <Empty>Ainda não há adaptações para redes.</Empty>}</div>
              <form action={saveDistributionAction} className="row" style={{ marginTop: 12 }}>
                <input type="hidden" name="id" value={s.id} />
                <select name="channel" aria-label="Canal" style={{ width: "auto" }}>{Object.entries(CHANNEL_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
                <input name="text" placeholder="Texto da publicação" aria-label="Texto" style={{ flex: "2 1 240px", width: "auto" }} />
                <input type="hidden" name="link" value={s.slug ? `/artigo/${s.slug}` : ""} />
                <button className="btn" type="submit">Nova adaptação</button>
              </form>
            </section>
          )}

          {s.state === "published" && (
            <section className="card" id="correcoes">
              <h2>Correções <span className="label">aparecem no fim do artigo</span></h2>
              <div className="list">{d.corrections.length ? d.corrections.map((c) => <div key={c.id}><span className="meta">{fmtDateTime(c.created_at)}</span><div>{c.text}</div></div>) : <Empty>Sem correções.</Empty>}</div>
              {isDesk(user.role) && <form action={addCorrectionAction} className="stack" style={{ marginTop: 10 }}>
                <input type="hidden" name="id" value={s.id} />
                <textarea name="text" placeholder="O que estava errado e o que foi corrigido" aria-label="Nota de correção" style={{ minHeight: 60 }} />
                <div><button className="btn" type="submit">Publicar correção</button></div></form>}
            </section>
          )}
        </div>

        <aside className="side">
          <section className="card" id="passo">
            <h2>Próximo passo</h2>
            {steps.length ? (
              <div className="stack" style={{ gap: 8 }}>
                {steps.filter((st) => st.to !== "scheduled").map((st) => (
                  <form key={st.to} action={transitionAction} className="stack" style={{ gap: 6 }}>
                    <input type="hidden" name="id" value={s.id} /><input type="hidden" name="to" value={st.to} />
                    <button className={`btn ${["approved", "pitch_approved", "published"].includes(st.to) ? "primary" : ""} ${st.to === "archived" ? "danger" : ""}`} type="submit">{st.label}</button>
                  </form>
                ))}
                {steps.some((st) => st.to === "scheduled") && (
                  <form action={transitionAction} className="stack" style={{ gap: 6 }}>
                    <input type="hidden" name="id" value={s.id} /><input type="hidden" name="to" value="scheduled" />
                    <label className="field"><span>Agendar para (hora de Lisboa)</span><input id="t-when" type="datetime-local" name="scheduled_at" required defaultValue={toLocalInput(s.scheduled_at)} /></label>
                    <button className="btn" type="submit">Agendar</button>
                  </form>
                )}
                {s.state === "in_review" && blockers.length > 0 && <p className="muted" style={{ fontSize: 13, margin: 0 }}>Antes de aprovar, resolve as afirmações por verificar.</p>}
              </div>
            ) : <Empty>{canWrite(user.role) ? "Não há passos que possas dar nesta fase." : "O teu papel é de leitura e revisão: deixa comentários."}</Empty>}
            {s.state === "scheduled" && s.scheduled_at && <p className="meta" style={{ marginTop: 10 }}>Publica-se a {fmtDateTime(s.scheduled_at)}.</p>}
            {s.approved_at && <p className="meta" style={{ marginTop: 6 }}>Aprovada por {nameOf(s.approved_by)} a {fmtDateTime(s.approved_at)}.</p>}
          </section>
          <section className="card">
            <h2>Histórico</h2>
            <ul className="timeline">{d.events.map((e) => (
              <li key={e.id}><b>{e.actor_label || (e.actor_kind === "system" ? "Sistema" : e.actor_kind)}</b>{" "}
                {e.type === "state_change" ? <>{e.from_state ? `${STATE_LABEL[e.from_state]} → ` : "criou como "}{e.to_state && STATE_LABEL[e.to_state]}</> : e.type === "assignment" ? "mudou o responsável" : e.type}
                {e.note && <div className="muted">«{e.note}»</div>}<div className="meta">{fmtDateTime(e.at)}</div></li>))}</ul>
          </section>
          <section className="card">
            <h2>Versões</h2>
            <p className="meta" style={{ marginTop: 0 }}><Link href={`/redacao/pecas/${s.id}/versoes`}>Comparar e restaurar</Link></p>
            <ul className="timeline">{d.versions.map((v) => <li key={v.version}><b>v{v.version}</b> · {v.name ?? v.saved_kind} · <span className="num">{v.words} palavras</span><div className="meta">{fmtDateTime(v.saved_at)}</div></li>)}</ul>
          </section>
        </aside>
      </div>
    </>
  );
}

/** Mostra uma proposta de agente: campos conhecidos com rótulos, o resto como lista legível. */
function OutputView({ payload }: { payload: Record<string, unknown> }) {
  const p = payload as Record<string, unknown>;
  const findings = Array.isArray(p.findings) ? (p.findings as { severity?: string; rule?: string; excerpt?: string; suggestion?: string; message?: string }[]) : [];
  const rest = Object.entries(p).filter(([k]) => !["findings", "cost", "run_id", "agent_id", "inputs"].includes(k));
  return (
    <div className="stack" style={{ marginTop: 10, gap: 8 }}>
      {findings.map((f, i) => (
        <div key={i} className={`finding ${f.severity ?? "info"}`}>
          <b>{f.rule ?? f.severity}</b>{f.excerpt && <> · «{f.excerpt}»</>}<div>{f.suggestion ?? f.message}</div>
        </div>
      ))}
      {rest.map(([k, v]) => (
        <div key={k}><span className="label">{k.replace(/_/g, " ")}</span><Value v={v} /></div>
      ))}
    </div>
  );
}

function Value({ v }: { v: unknown }): React.ReactNode {
  if (v == null || v === "") return <span className="muted"> —</span>;
  if (typeof v === "string") return /^https?:\/\//.test(v) ? <div><a href={v} target="_blank" rel="noreferrer">{v}</a></div> : <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{v}</div>;
  if (typeof v !== "object") return <div>{String(v)}</div>;
  if (Array.isArray(v)) return <ul style={{ margin: "4px 0", paddingLeft: 18 }}>{v.slice(0, 40).map((x, i) => <li key={i}><Value v={x} /></li>)}</ul>;
  return <div style={{ paddingLeft: 10, borderLeft: "2px solid var(--line)" }}>{Object.entries(v).slice(0, 30).map(([k, x]) => <div key={k}><span className="muted">{k.replace(/_/g, " ")}:</span> <Value v={x} /></div>)}</div>;
}
