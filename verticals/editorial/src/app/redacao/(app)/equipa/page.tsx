import Link from "next/link";
import { Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { isLead, ROLE_LABEL, ROLES } from "@/lib/context";
import { withCtx } from "@/lib/db";
import { listTeam } from "@/lib/queries";
import { addMemberAction } from "../../actions";

const ROLE_HELP: Record<string, string> = {
  admin: "Tudo, incluindo papéis de administração.", director: "Linha editorial, equipa, configuração, aprovação e publicação.",
  editor: "Aprova pautas e artigos, agenda e publica.", journalist: "Propõe pautas, investiga e escreve as suas peças.",
  contributor: "Como jornalista, para colaborações pontuais.", reviewer: "Lê e comenta; não altera peças.",
};

export default async function Equipa({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { user, ctx } = await requireUser();
  const sp = await searchParams;
  const team = await withCtx(ctx, (tx) => listTeam(tx));
  const lead = isLead(user.role);
  return (
    <>
      <div className="nr-head"><div><p className="label">Redação</p><h1>Equipa</h1></div></div>
      <Flash sp={sp} />
      <section className="card">
        <div className="table-wrap">
          <table className="t">
            <thead><tr><th>Pessoa</th><th>Papel</th><th className="hide-sm">Email</th><th className="hide-sm">Autor</th><th><span className="sr-only">Acções</span></th></tr></thead>
            <tbody>{team.map((m) => (
              <tr key={m.user_id}>
                <td><b>{m.name}</b>{m.user_id === user.userId && <span className="label"> (tu)</span>}<div className="meta show-sm">{m.email}</div></td>
                <td>{ROLE_LABEL[m.role]}</td>
                <td className="hide-sm">{m.email}</td>
                <td className="hide-sm">{m.public_profile ? <a href={`/autor/${m.author_slug}`}>/autor/{m.author_slug}</a> : <span className="muted">privado</span>}</td>
                <td style={{ textAlign: "right" }}>{(lead || m.user_id === user.userId)
                  ? <Link className="btn small" href={`/redacao/equipa/${m.user_id}`}>{lead ? "Editar" : "A minha ficha"}</Link> : null}</td>
              </tr>))}</tbody>
          </table>
        </div>
        <details className="box" style={{ marginTop: 12 }}><summary>O que cada papel pode fazer</summary>
          <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>{ROLES.map((r) => <li key={r}><b>{ROLE_LABEL[r]}</b>: {ROLE_HELP[r]}</li>)}</ul>
        </details>
      </section>
      {lead && (
        <section className="card" style={{ marginTop: 16, maxWidth: 760 }}>
          <h2>Acrescentar pessoa</h2>
          <form action={addMemberAction} className="stack">
            <div className="grid2">
              <label className="field"><span>Nome</span><input id="m-name" name="name" required /></label>
              <label className="field"><span>Email</span><input id="m-email" name="email" type="email" required /></label>
              <label className="field"><span>Papel</span><select id="m-role" name="role" defaultValue="journalist">{ROLES.filter((r) => r !== "admin" || user.role === "admin").map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}</select></label>
              <label className="field"><span>Palavra-passe inicial</span><input id="m-pass" name="password" type="password" minLength={10} required autoComplete="new-password" /><small>A pessoa muda-a em «Conta».</small></label>
            </div>
            <div><button className="btn primary" type="submit">Acrescentar à equipa</button></div>
          </form>
        </section>
      )}
    </>
  );
}
