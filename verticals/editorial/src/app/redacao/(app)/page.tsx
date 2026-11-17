import Link from "next/link";
import { Empty, Flash, SectionTag, StateLine, StatePill } from "@/components/dashboard-bits";
import { requireUser } from "@/lib/auth";
import { isDesk } from "@/lib/context";
import { fmtDateTime, relTime } from "@/lib/format";
import { dashboard } from "@/lib/queries";
import { STATE_LABEL } from "@/lib/workflow";

export default async function Dashboard({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { user, ctx } = await requireUser();
  const sp = await searchParams;
  const d = await dashboard(ctx);
  const c = (k: keyof typeof d.counts) => d.counts[k] ?? 0;
  const inProduction = c("researching") + c("interviewing") + c("writing");
  const desk = isDesk(user.role);
  return (
    <>
      <div className="nr-head">
        <div>
          <p className="label">Painel</p>
          <h1>Bom trabalho, {user.name.split(" ")[0]}</h1>
        </div>
        <div className="row">
          <Link className="btn primary" href="/redacao/pautas/nova">Nova pauta</Link>
          <Link className="btn" href="/redacao/radar">Ver radar{d.radarNew ? ` (${d.radarNew})` : ""}</Link>
        </div>
      </div>
      <Flash sp={sp} />

      <section className="kpis" aria-label="Produção">
        <Link className="kpi" href="/redacao/pautas?estado=pitch_proposed"><span className="label">Pautas propostas</span><b>{c("pitch_proposed")}</b></Link>
        <Link className="kpi" href="/redacao/pautas?estado=idea"><span className="label">Ideias no banco</span><b>{c("idea")}</b></Link>
        <Link className="kpi" href="/redacao/pautas?vista=quadro"><span className="label">Em produção</span><b>{inProduction}</b></Link>
        <Link className="kpi" href="/redacao/pautas?estado=in_review"><span className="label">Em revisão</span><b>{c("in_review")}</b></Link>
        <Link className="kpi" href="/redacao/pautas?estado=scheduled"><span className="label">Agendadas</span><b>{c("scheduled")}</b></Link>
        <Link className="kpi" href="/redacao/pautas?estado=published"><span className="label">Publicadas (7 dias)</span><b>{d.publishedWeek}</b></Link>
        {d.overdue.length > 0 && <a className="kpi alert" href="#atrasadas"><span className="label">Com prazo ultrapassado</span><b>{d.overdue.length}</b></a>}
        {d.suggestions > 0 && <Link className="kpi" href="/redacao/radar#propostas"><span className="label">Propostas dos agentes</span><b>{d.suggestions}</b></Link>}
      </section>

      <div className="cards">
        <section className="card">
          <h2>O meu trabalho <span className="label">{d.mine.length}</span></h2>
          <div className="list">{d.mine.length ? d.mine.map((s) => <StateLine key={s.id} s={s} />) : <Empty>Não tens peças atribuídas. Pega numa pauta aprovada ou propõe uma.</Empty>}</div>
        </section>
        <section className="card">
          <h2>{desk ? "À espera da tua revisão" : "Em revisão"} <span className="label">{d.review.length}</span></h2>
          <div className="list">{d.review.length ? d.review.map((s) => <StateLine key={s.id} s={s} show="none" />) : <Empty>Nada em revisão.</Empty>}</div>
        </section>
        <section className="card">
          <h2>Pautas propostas <span className="label">{d.pitches.length}</span></h2>
          <div className="list">{d.pitches.length ? d.pitches.map((s) => <StateLine key={s.id} s={s} show="none" />) : <Empty>Sem pautas à espera de decisão.</Empty>}</div>
        </section>
        <section className="card">
          <h2>Agendadas</h2>
          <div className="list">{d.scheduled.length ? d.scheduled.map((s) => (
            <div key={s.id}>
              <Link className="item-title" href={`/redacao/pecas/${s.id}`}>{s.title}</Link>
              <div className="meta"><span className="num">{fmtDateTime(s.scheduled_at)}</span><SectionTag name={s.section_name} color={s.section_color} /></div>
            </div>)) : <Empty>Nada agendado.</Empty>}</div>
        </section>
        {d.overdue.length > 0 && (
          <section className="card" id="atrasadas">
            <h2>Prazo ultrapassado</h2>
            <div className="list">{d.overdue.map((s) => <StateLine key={s.id} s={s} />)}</div>
          </section>
        )}
        <section className="card">
          <h2>Publicadas recentemente</h2>
          <div className="list">{d.recent.length ? d.recent.map((s) => (
            <div key={s.id}>
              <Link className="item-title" href={`/redacao/pecas/${s.id}`}>{s.title}</Link>
              <div className="meta"><span>{relTime(s.published_at)}</span>{s.slug && <a href={`/artigo/${s.slug}`} target="_blank" rel="noreferrer">Ver no site</a>}</div>
            </div>)) : <Empty>Ainda não há nada publicado.</Empty>}</div>
        </section>
        <section className="card">
          <h2>Atividade da equipa</h2>
          <ul className="timeline">{d.activity.length ? d.activity.map((a, i) => (
            <li key={i}>
              <b>{a.actor_label || (a.actor_kind === "system" ? "Sistema" : "Agente")}</b>{" "}
              {a.type === "state_change" && a.to_state ? <>passou para <StatePill state={a.to_state} /></> : a.type === "assignment" ? "atribuiu" : a.type}
              {" "}<Link href={`/redacao/pecas/${a.story_id}`}>{a.title}</Link>
              <div className="meta">{relTime(a.at)}</div>
            </li>)) : <li className="empty">Sem atividade ainda.</li>}</ul>
        </section>
      </div>
      <p className="muted" style={{ fontSize: 13, marginTop: 18 }}>Estados: {Object.values(STATE_LABEL).join(" → ")}.</p>
    </>
  );
}
