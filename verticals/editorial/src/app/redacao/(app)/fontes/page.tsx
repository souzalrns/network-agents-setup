import { Empty, Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { CONF_LABEL } from "@/lib/constants";
import { canWrite } from "@/lib/context";
import { listSources } from "@/lib/queries";
import { saveSourceAction } from "../../actions";

export default async function Fontes({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { user, ctx } = await requireUser();
  const sp = await searchParams;
  const q = typeof sp.q === "string" ? sp.q.slice(0, 100) : "";
  const rows = await listSources(ctx, q);
  return (
    <>
      <div className="nr-head"><div><p className="label">Fontes jornalísticas</p><h1>Fontes</h1></div></div>
      <Flash sp={sp} />
      <p className="muted" style={{ marginTop: 0, maxWidth: "70ch" }}>As fontes são da equipa. Os agentes, o sistema e o público nunca as vêem. Uma fonte <b>protegida</b> só é visível para quem a registou e para a direção.</p>
      <form className="filters" method="get"><input type="search" name="q" defaultValue={q} placeholder="Procurar por nome ou organização" aria-label="Procurar" /><button className="btn" type="submit">Procurar</button></form>
      <section className="card table-wrap">
        {rows.length ? (
          <table className="t"><thead><tr><th>Nome</th><th>Organização</th><th>Contacto</th><th>Confidencialidade</th><th>Registada por</th><th className="num">Peças</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.id}><td><b>{r.name}</b>{r.notes && <div className="muted" style={{ fontSize: 13 }}>{r.notes}</div>}</td><td>{r.organization}</td><td>{r.contact}</td>
                <td>{CONF_LABEL[r.confidentiality]}</td><td>{r.owner_name}</td><td className="num">{r.stories}</td></tr>))}</tbody></table>
        ) : <Empty>Ainda não há fontes registadas{q ? " com esse nome" : ""}.</Empty>}
      </section>
      {canWrite(user.role) && (
        <section className="card" style={{ marginTop: 14, maxWidth: 860 }}>
          <h2>Nova fonte</h2>
          <form action={saveSourceAction} className="stack">
            <input type="hidden" name="back" value="/redacao/fontes" />
            <div className="grid2">
              <label className="field"><span>Nome</span><input id="s-name" name="name" required /></label>
              <label className="field"><span>Organização</span><input id="s-org" name="organization" /></label>
              <label className="field"><span>Tipo</span><select id="s-kind" name="kind"><option value="person">Pessoa</option><option value="institution">Instituição</option><option value="document">Documento</option></select></label>
              <label className="field"><span>Confidencialidade</span><select id="s-conf" name="confidentiality" defaultValue="internal">{Object.entries(CONF_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
            </div>
            <label className="field"><span>Contacto</span><input id="s-contact" name="contact" /></label>
            <label className="field"><span>Notas</span><textarea id="s-notes" name="notes" /></label>
            <div><button className="btn primary" type="submit">Guardar fonte</button></div>
          </form>
        </section>
      )}
    </>
  );
}
