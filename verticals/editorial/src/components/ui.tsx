import Link from "next/link";
import { STATE_LABEL, type State } from "@/lib/workflow";

export const STATE_COLOR: Record<State, string> = {
  idea: "var(--s-idea)", pitch_proposed: "var(--s-pitch)", pitch_approved: "var(--s-approvedpitch)",
  researching: "var(--s-research)", interviewing: "var(--s-interview)", writing: "var(--s-writing)",
  in_review: "var(--s-review)", approved: "var(--s-approved)", scheduled: "var(--s-scheduled)",
  published: "var(--s-published)", archived: "var(--s-archived)",
};

export function StatePill({ state }: { state: State }) {
  return <span className="pill" style={{ "--c": STATE_COLOR[state] } as React.CSSProperties}>{STATE_LABEL[state]}</span>;
}

export function SectionTag({ name, color }: { name: string | null; color: string | null }) {
  if (!name) return <span className="muted">Sem editoria</span>;
  return <span className="sec" style={{ "--c": color ?? "var(--muted)" } as React.CSSProperties}>{name}</span>;
}

export function Flash({ sp }: { sp: Record<string, string | string[] | undefined> }) {
  const ok = typeof sp.ok === "string" ? sp.ok : null;
  const erro = typeof sp.erro === "string" ? sp.erro : null;
  return (
    <>
      {erro && <div className="flash erro" role="alert">{erro}</div>}
      {ok && <div className="flash ok" role="status">{ok}</div>}
    </>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="empty">{children}</p>;
}

export function StoryLine({ s, show = "state" }: {
  s: { id: string; title: string; state: State; priority: number; section_name: string | null; section_color: string | null;
    assignee_name?: string | null; due_date?: string | null; origin?: string };
  show?: "state" | "none";
}) {
  return (
    <div>
      <Link className="item-title" href={`/redacao/pecas/${s.id}`}>{s.title}</Link>
      <div className="meta">
        {show === "state" && <StatePill state={s.state} />}
        <SectionTag name={s.section_name} color={s.section_color} />
        {s.priority === 1 && <span className="prio1">Prioritária</span>}
        {s.assignee_name ? <span>{s.assignee_name}</span> : <span>Por atribuir</span>}
        {s.due_date && <span className="num">Prazo {s.due_date.split("-").reverse().join("/")}</span>}
        {s.origin && s.origin !== "human" && <span>Sugerida pelo {s.origin === "radar" ? "radar" : "agente"}</span>}
      </div>
    </div>
  );
}
