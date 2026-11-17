import Link from "next/link";
import { Empty, Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { fmtDateTime } from "@/lib/format";
import { listActivity, listTeam } from "@/lib/queries";
import { STATE_LABEL } from "@/lib/workflow";

type SP = Record<string, string | string[] | undefined>;
const one = (v: string | string[] | undefined) => (typeof v === "string" ? v : "");
const TYPES: Record<string, string> = { state_change: "Mudanças de estado", published_edit: "Edições de publicadas", assignment: "Atribuições" };
const KINDS: Record<string, string> = { human: "Pessoas", agent: "Agentes", system: "Sistema" };

/** Actividade da redacção: o registo que a base de dados escreve (quem, o quê, quando, porquê), filtrável e paginado. */
export default async function Atividade({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const { ctx } = await requireUser();
  const f = { type: TYPES[one(sp.tipo)] ? one(sp.tipo) : "", kind: KINDS[one(sp.quem)] ? one(sp.quem) : "",
    actor: /^[0-9a-f-]{36}$/i.test(one(sp.pessoa)) ? one(sp.pessoa) : "", before: Number(one(sp.antes)) || 0, limit: 50 };
  const { rows, team } = await withCtx(ctx, async (tx) => ({ rows: await listActivity(tx, f), team: await listTeam(tx) }));
  const more = rows.length > f.limit;
  const shown = rows.slice(0, f.limit);
  const qs = (patch: Record<string, string>) => {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries({ tipo: f.type, quem: f.kind, pessoa: f.actor, ...patch })) if (v) p.set(k, v);
    return `/redacao/atividade?${p}`;
  };
  let day = "";
  return (
    <>
      <div className="nr-head"><div><p className="label">Redação</p><h1>Atividade</h1></div></div>
      <Flash sp={sp} />
      <form className="filters" method="get">
        <select name="tipo" defaultValue={f.type} aria-label="Tipo"><option value="">Tudo</option>{Object.entries(TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <select name="quem" defaultValue={f.kind} aria-label="Quem"><option value="">Pessoas, agentes e sistema</option>{Object.entries(KINDS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <select name="pessoa" defaultValue={f.actor} aria-label="Pessoa"><option value="">Toda a equipa</option>{team.map((m) => <option key={m.user_id} value={m.user_id}>{m.name}</option>)}</select>
        <button className="btn" type="submit">Filtrar</button>
      </form>
      <section className="card">
        {shown.length ? (
          <ul className="timeline activity">{shown.map((e) => {
            const d = new Date(e.at).toLocaleDateString("pt-PT", { weekday: "long", day: "numeric", month: "long", timeZone: "Europe/Lisbon" });
            const head = d !== day ? (day = d) : null;
            return (
              <li key={e.id}>
                {head && <div className="label day-head">{head}</div>}
                <b>{e.actor_label || (e.actor_kind === "system" ? "Sistema" : e.actor_kind)}</b>{" "}
                {e.type === "state_change" ? <>{e.from_state ? <>passou <Link href={`/redacao/pecas/${e.story_id}`}>{e.title}</Link> de {STATE_LABEL[e.from_state]} para <b>{e.to_state && STATE_LABEL[e.to_state]}</b></> : <>criou <Link href={`/redacao/pecas/${e.story_id}`}>{e.title}</Link></>}</>
                  : e.type === "published_edit" ? <>alterou a peça publicada <Link href={`/redacao/pecas/${e.story_id}/versoes?a=${String(e.payload.from_version ?? "")}&b=${String(e.payload.to_version ?? "")}`}>{e.title}</Link></>
                  : e.type === "assignment" ? <>mudou o responsável de <Link href={`/redacao/pecas/${e.story_id}`}>{e.title}</Link></>
                  : <>{e.type} em <Link href={`/redacao/pecas/${e.story_id}`}>{e.title}</Link></>}
                {e.note && <div className="muted">«{e.note}»</div>}
                <div className="meta">{fmtDateTime(e.at)}</div>
              </li>
            );
          })}</ul>
        ) : <Empty>Sem atividade com estes filtros.</Empty>}
        {(more || f.before > 0) && (
          <nav className="pager" aria-label="Páginas">
            {f.before > 0 ? <Link className="btn small" href={qs({})}>← Mais recentes</Link> : <span />}
            {more ? <Link className="btn small" href={qs({ antes: String(shown.at(-1)!.id) })}>Mais antigas →</Link> : <span />}
          </nav>
        )}
      </section>
    </>
  );
}
