import Link from "next/link";
import { Empty, Flash, STATE_COLOR, StoryLine } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { countStoriesTx, listSections, listStoriesTx, listTeam, type StoryFilter, type StoryRow } from "@/lib/queries";
import { DESK_STATES, isState, nextSteps, PITCH_STATES, STATE_LABEL, STATES, type State, WORK_STATES } from "@/lib/workflow";
import { transitionAction } from "../../actions";
import { Board } from "./board";

type SP = Record<string, string | string[] | undefined>;
const one = (v: string | string[] | undefined) => (typeof v === "string" ? v : "");
const PAGE = 25;

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
  const pessoa = one(sp.pessoa), prio = Number(one(sp.prioridade)), ordem = one(sp.ordem);
  const page = Math.max(1, Math.min(1000, Number(one(sp.pagina)) || 1));
  const filtro: StoryFilter = { state: (isState(estado) ? estado : estado === "todas" ? "" : "active") as State | "active" | "",
    section: one(sp.editoria) || undefined, q: one(sp.q) || undefined, mine: one(sp.minhas) === "1" ? user.userId : undefined,
    assignee: pessoa === "none" || /^[0-9a-f-]{36}$/i.test(pessoa) ? pessoa : undefined, priority: [1, 2, 3].includes(prio) ? prio : undefined,
    sort: ordem === "recentes" || ordem === "prazo" ? ordem : "prioridade" };
  const { rows, sections, total, team } = await withCtx(ctx, async (tx) => {
    const board = vista === "quadro";
    const f = board ? { ...filtro, state: estado === "todas" ? "" : filtro.state === "active" ? "" : filtro.state, limit: 400 }
      : { ...filtro, limit: PAGE, offset: (page - 1) * PAGE };
    return { rows: await listStoriesTx(tx, f), sections: await listSections(tx), total: board ? 0 : await countStoriesTx(tx, filtro), team: await listTeam(tx) };
  });
  const pages = Math.max(1, Math.ceil(total / PAGE));
  const qs = (patch: Record<string, string>) => {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries({ vista, estado, editoria: one(sp.editoria), q: one(sp.q), minhas: one(sp.minhas), pessoa, prioridade: one(sp.prioridade), ordem, pagina: "", ...patch })) if (v) p.set(k, v);
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
        <select name="pessoa" defaultValue={pessoa} aria-label="Pessoa">
          <option value="">Toda a equipa</option><option value="none">Sem responsável</option>
          {team.filter((m) => m.role !== "reviewer").map((m) => <option key={m.user_id} value={m.user_id}>{m.name}</option>)}
        </select>
        <select name="prioridade" defaultValue={one(sp.prioridade)} aria-label="Prioridade">
          <option value="">Qualquer prioridade</option><option value="1">Alta</option><option value="2">Normal</option><option value="3">Baixa</option>
        </select>
        <select name="ordem" defaultValue={ordem || "prioridade"} aria-label="Ordenar">
          <option value="prioridade">Por prioridade</option><option value="prazo">Por prazo</option><option value="recentes">Mexidas há menos tempo</option>
        </select>
        <label className="check"><input type="checkbox" name="minhas" value="1" defaultChecked={one(sp.minhas) === "1"} /> Só as minhas</label>
        <button className="btn" type="submit">Filtrar</button>
      </form>

      {vista === "lista" ? (
        <section className="card">
          <p className="label" style={{ marginTop: 0 }}>{total} {total === 1 ? "peça" : "peças"}{pages > 1 && ` · página ${page} de ${pages}`}</p>
          <div className="list">{rows.length ? rows.map((s) => <StoryLine key={s.id} s={s} />) : <Empty>Nenhuma peça com estes filtros.</Empty>}</div>
          {pages > 1 && (
            <nav className="pager" aria-label="Páginas">
              {page > 1 ? <Link className="btn small" href={qs({ pagina: String(page - 1) })} rel="prev">← Anterior</Link> : <span />}
              <span className="muted">{(page - 1) * PAGE + 1}–{Math.min(total, page * PAGE)} de {total}</span>
              {page < pages ? <Link className="btn small" href={qs({ pagina: String(page + 1) })} rel="next">Seguinte →</Link> : <span />}
            </nav>
          )}
        </section>
      ) : (
        <Board back={qs({})} action={transitionAction} columns={COLUMNS.map((col) => ({
          title: col.title, states: col.states, color: STATE_COLOR[col.states[0]!],
          items: rows.filter((r: StoryRow) => col.states.includes(r.state)).map((r) => ({
            id: r.id, title: r.title, state: r.state, priority: r.priority, section_name: r.section_name, section_color: r.section_color,
            assignee_name: r.assignee_name, due_date: r.due_date, origin: r.origin,
            targets: nextSteps(r.state, user.role, user.userId, { assigneeId: r.assignee_id, authorId: r.author_id, createdBy: r.created_by })
              .filter((t) => t.to !== "scheduled").map((t) => ({ to: t.to, label: t.label })),
          })),
        }))} />
      )}
    </>
  );
}
