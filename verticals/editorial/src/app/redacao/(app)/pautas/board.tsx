"use client";
import Link from "next/link";
import { useRef, useState, useTransition } from "react";
import { STATE_LABEL, type State } from "@/lib/workflow";

/**
 * Quadro de pautas com movimentação segura (D3).
 * Arrastar um cartão NÃO muda o estado por si: o cartão só oferece os destinos que o fluxo já permite a esta
 * pessoa (nextSteps, calculado no servidor), e largar chama a mesma acção dos botões da peça. A base de dados
 * volta a decidir (quatro olhos, afirmações, aprovação presa ao conteúdo). Sem rato ou no telemóvel, cada cartão
 * tem «Mover para…», que faz o mesmo.
 */
type Target = { to: string; label: string };
type Item = { id: string; title: string; state: string; priority: number; section_name: string | null; section_color: string | null;
  assignee_name: string | null; due_date: string | null; origin: string; targets: Target[] };
type Column = { title: string; states: string[]; color: string; items: Item[] };

export function Board({ columns, action, back }: { columns: Column[]; action: (f: FormData) => void | Promise<void>; back: string }) {
  const [drag, setDrag] = useState<Item | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const [choose, setChoose] = useState<{ item: Item; options: Target[] } | null>(null);
  const [pending, start] = useTransition();
  const live = useRef<HTMLParagraphElement>(null);

  const move = (item: Item, to: string) => {
    const f = new FormData();
    f.set("id", item.id); f.set("to", to); f.set("back", back); f.set("title", item.title);
    start(() => action(f));
  };
  const targetsIn = (item: Item | null, col: Column) => (item ? item.targets.filter((t) => col.states.includes(t.to)) : []);
  const drop = (col: Column) => {
    const item = drag;
    setDrag(null); setOver(null);
    if (!item) return;
    const options = targetsIn(item, col);
    if (!options.length) {
      if (live.current) live.current.textContent = col.states.includes(item.state) ? "" : `«${item.title}» não pode ir para ${col.title} a partir daqui.`;
      return;
    }
    if (options.length === 1) move(item, options[0]!.to);
    else setChoose({ item, options });
  };

  return (
    <>
      <p ref={live} className="muted" role="status" aria-live="polite" style={{ minHeight: 20, margin: "0 0 8px" }}>
        {pending ? "A mudar o estado…" : drag ? `A mover «${drag.title}»: as colunas assinaladas são os destinos possíveis.` : "Arrasta um cartão para outra coluna, ou usa «Mover para…»."}
      </p>
      <div className="board" aria-busy={pending}>
        {columns.map((col) => {
          const allowed = targetsIn(drag, col).length > 0;
          return (
            <section key={col.title} className={`col${drag ? (allowed ? " can-drop" : " no-drop") : ""}${over === col.title && allowed ? " over" : ""}`}
              style={{ "--c": col.color } as React.CSSProperties} aria-label={col.title}
              onDragOver={(e) => { if (allowed) { e.preventDefault(); e.dataTransfer.dropEffect = "move"; setOver(col.title); } }}
              onDragLeave={() => setOver((o) => (o === col.title ? null : o))}
              onDrop={(e) => { e.preventDefault(); drop(col); }}>
              <h3>{col.title} <span className="muted num">{col.items.length}</span></h3>
              {col.items.length ? col.items.map((s) => (
                <div key={s.id} className={`tile${drag?.id === s.id ? " dragging" : ""}`} draggable={s.targets.length > 0}
                  onDragStart={(e) => { e.dataTransfer.setData("text/plain", s.id); e.dataTransfer.effectAllowed = "move"; setDrag(s); }}
                  onDragEnd={() => { setDrag(null); setOver(null); }}>
                  <Link className="item-title" href={`/redacao/pecas/${s.id}`}>{s.title}</Link>
                  <div className="meta">
                    {col.states.length > 1 && <span className="label">{STATE_LABEL[s.state as State]}</span>}
                    {s.section_name && <span className="sec" style={{ "--c": s.section_color ?? "var(--muted)" } as React.CSSProperties}>{s.section_name}</span>}
                    {s.priority === 1 && <span className="prio1">Prioritária</span>}
                    <span>{s.assignee_name ?? "Por atribuir"}</span>
                    {s.due_date && <span className="num">Prazo {s.due_date.split("-").reverse().join("/")}</span>}
                  </div>
                  {s.targets.length > 0 && (
                    <form className="move" onSubmit={(e) => { e.preventDefault(); const to = new FormData(e.currentTarget).get("to"); if (to) move(s, String(to)); }}>
                      <select name="to" aria-label={`Mover «${s.title}» para`} defaultValue="">
                        <option value="" disabled>Mover para…</option>
                        {s.targets.map((t) => <option key={t.to} value={t.to}>{t.label}</option>)}
                      </select>
                      <button className="btn small" type="submit" disabled={pending}>Mover</button>
                    </form>
                  )}
                </div>
              )) : <p className="empty">Nada aqui.</p>}
            </section>
          );
        })}
      </div>
      {choose && (
        <div className="notice-box" role="dialog" aria-label="Escolher o passo" style={{ marginTop: 12 }}>
          <b>«{choose.item.title}»</b>: qual destes passos?
          <div className="row" style={{ marginTop: 8 }}>
            {choose.options.map((o) => <button key={o.to} type="button" className="btn small" onClick={() => { setChoose(null); move(choose.item, o.to); }}>{o.label}</button>)}
            <button type="button" className="btn small" onClick={() => setChoose(null)}>Cancelar</button>
          </div>
        </div>
      )}
    </>
  );
}
