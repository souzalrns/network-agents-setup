import Link from "next/link";
import { Empty, Flash, STATE_COLOR, StoryLine } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { listSections, listStoriesTx, type StoryRow } from "@/lib/queries";
import { DESK_STATES, isState, PITCH_STATES, STATE_LABEL, STATES, type State, WORK_STATES } from "@/lib/workflow";

type SP = Record<string, string | string[] | undefined>;
const one = (v: string | string[] | undefined) => (typeof v === "string" ? v : "");

const COLUMNS: { title: string; states: State[] }[] = [
  { title: "Banco de ideias", states: ["idea"] },
  { title: "Pautas", states: PITCH_STATES.filter((s) => s !== "idea") },
  { title: "Em produção", states: WORK_STATES },
  { title: "Edição", states: DESK_STATES },
  { title: "Publicadas", states: ["published"] },
];

export default async function Pautas({ searchParams }: { searchParams: Promise<SP> }) {
  const { user, ctx } = await requireUser();
  const sp = await searchParams;
  const vista = one(sp.vista) === "quadro" ? "quadro" : "lista";
  const estado = one(sp.estado);
  const filtro = { state: (isState(estado) ? estado : estado === "todas" ? "" : "active") as State | "active" | "",
    section: one(sp.editoria) || undefined, q: one(sp.q) || undefined, mine: one(sp.minhas) === "1" ? user.userId : undefined };
  const { rows, sections } = await withCtx(ctx, async (tx) => ({
    rows: await listStoriesTx(tx, vista === "quadro" ? { ...filtro, state: estado === "todas" ? "" : filtro.state === "active" ? "" : filtro.state, limit: 400 } : filtro),
    sections: await listSections(tx),
  }));
  const qs = (patch: Record<string, string>) => {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries({ vista, estado, editoria: one(sp.editoria), q: one(sp.q), minhas: one(sp.minhas), ...patch })) if (v) p.set(k, v);
    return `/redacao/pautas?${p}`;
  };
  return (
    <>
      <div className="nr-head">
        <div><p className="label">Banco de pautas</p><h1>Pautas e peças</h1></div>
        <Link className="btn primary" href="/redacao/pautas/nova">Nova pauta</Link>
      </div>
      <Flash sp={sp} />
      <nav className="tabs" aria-label="Vista">
        <Link href={qs({ vista: "lista" })} aria-current={vista === "lista" ? "page" : undefined}>Lista</Link>
        <Link href={qs({ vista: "quadro" })} aria-current={vista === "quadro" ? "page" : undefined}>Quadro</Link>
      </nav>
      <form className="filters" method="get">
        <input type="hidden" name="vista" value={vista} />
        <input type="search" name="q" defaultValue={one(sp.q)} placeholder="Procurar por título ou texto" aria-label="Procurar" />
        <select name="estado" defaultValue={estado || "active"} aria-label="Estado">
          <option value="active">Em curso (sem publicadas e arquivadas)</option>
          <option value="todas">Todos os estados</option>
          {STATES.map((s) => <option key={s} value={s}>{STATE_LABEL[s]}</option>)}
        </select>
        <select name="editoria" defaultValue={one(sp.editoria)} aria-label="Editoria">
          <option value="">Todas as editorias</option>
          {sections.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <label className="check"><input type="checkbox" name="minhas" value="1" defaultChecked={one(sp.minhas) === "1"} /> Só as minhas</label>
        <button className="btn" type="submit">Filtrar</button>
      </form>

      {vista === "lista" ? (
        <section className="card">
          <p className="label" style={{ marginTop: 0 }}>{rows.length} {rows.length === 1 ? "peça" : "peças"}</p>
          <div className="list">{rows.length ? rows.map((s) => <StoryLine key={s.id} s={s} />) : <Empty>Nenhuma peça com estes filtros.</Empty>}</div>
        </section>
      ) : (
        <div className="board">
          {COLUMNS.map((col) => {
            const items = rows.filter((r: StoryRow) => col.states.includes(r.state));
            return (
              <section className="col" key={col.title} style={{ "--c": STATE_COLOR[col.states[0]!] } as React.CSSProperties}>
                <h3>{col.title} <span className="muted num">{items.length}</span></h3>
                {items.length ? items.map((s) => <div className="tile" key={s.id}><StoryLine s={s} /></div>) : <p className="empty">Nada aqui.</p>}
              </section>
            );
          })}
        </div>
      )}
    </>
  );
}
