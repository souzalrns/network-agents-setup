import Link from "next/link";
import { Flash, StatePill } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { fmtDate } from "@/lib/format";
import type { State } from "@/lib/workflow";

const DAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

function monday(d: Date): Date {
  const x = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  x.setUTCDate(x.getUTCDate() - ((x.getUTCDay() + 6) % 7));
  return x;
}
const iso = (d: Date) => d.toISOString().slice(0, 10);

export default async function Calendario({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { ctx } = await requireUser();
  const sp = await searchParams;
  const base = typeof sp.semana === "string" && /^\d{4}-\d{2}-\d{2}$/.test(sp.semana) ? new Date(`${sp.semana}T00:00:00Z`) : new Date();
  const start = monday(base);
  const end = new Date(start); end.setUTCDate(end.getUTCDate() + 7);
  const prev = new Date(start); prev.setUTCDate(prev.getUTCDate() - 7);
  const rows = await withCtx(ctx, (tx) => tx<{ id: string; title: string; state: State; day: string; kind: string; section: string | null; color: string | null }[]>`
    select s.id, s.title, s.state, coalesce(to_char(s.published_at at time zone 'Europe/Lisbon', 'YYYY-MM-DD'),
      to_char(s.scheduled_at at time zone 'Europe/Lisbon', 'YYYY-MM-DD'), s.due_date::text) as day,
      case when s.published_at is not null then 'publicada' when s.scheduled_at is not null then 'agendada' else 'prazo' end as kind,
      sec.name as section, sec.color
    from stories s left join sections sec on sec.id = s.section_id
    where s.state <> 'archived' and (
      (s.published_at >= ${start} and s.published_at < ${end}) or (s.scheduled_at >= ${start} and s.scheduled_at < ${end})
      or (s.due_date >= ${iso(start)}::date and s.due_date < ${iso(end)}::date and s.state not in ('published', 'scheduled')))
    order by day`);
  const today = new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Lisbon" }).format(new Date());
  return (
    <>
      <div className="nr-head">
        <div><p className="label">Calendário editorial</p><h1>Semana de {fmtDate(start, { day: "numeric", month: "long" })}</h1></div>
        <div className="row">
          <Link className="btn" href={`/redacao/calendario?semana=${iso(prev)}`}>← Anterior</Link>
          <Link className="btn" href="/redacao/calendario">Esta semana</Link>
          <Link className="btn" href={`/redacao/calendario?semana=${iso(end)}`}>Seguinte →</Link>
        </div>
      </div>
      <Flash sp={sp} />
      <p className="muted" style={{ marginTop: 0 }}>Mostra o que foi publicado, o que está agendado e os prazos das peças em curso. A meta é 5 a 7 peças principais por semana.</p>
      <div className="cal">
        {DAYS.map((name, i) => {
          const day = new Date(start); day.setUTCDate(day.getUTCDate() + i);
          const key = iso(day);
          const items = rows.filter((r) => r.day === key);
          return (
            <section key={key} className={`day ${key === today ? "today" : ""}`}>
              <header>{name} <span className="muted num">{fmtDate(day, { day: "numeric", month: "short", timeZone: "UTC" })}</span></header>
              {items.map((r) => (
                <div key={r.id} className="tile" style={{ padding: 8 }}>
                  <Link className="item-title" href={`/redacao/pecas/${r.id}`} style={{ fontSize: 14 }}>{r.title}</Link>
                  <div className="meta"><StatePill state={r.state} /><span>{r.kind}</span></div>
                </div>
              ))}
            </section>
          );
        })}
      </div>
      <p className="muted" style={{ fontSize: 14 }}>{rows.length} {rows.length === 1 ? "peça" : "peças"} nesta semana.</p>
    </>
  );
}
