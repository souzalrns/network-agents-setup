import { Empty } from "@/components/ui";
import { requireLead } from "@/lib/auth";
import { fmtDateTime } from "@/lib/format";
import { listSubscribers } from "@/lib/newsletter";

/** Newsletter: a lista (só a direção vê), com exportação para qualquer serviço de envio. */
export default async function NewsletterAdmin() {
  const { ctx } = await requireLead();
  const rows = await listSubscribers(ctx);
  const active = rows.filter((r) => r.status === "active");
  return (
    <>
      <div className="nr-head"><div><p className="label">Direção</p><h1>Newsletter</h1></div>
        {active.length > 0 && <a className="btn primary" href="/redacao/exportar/newsletter">Exportar inscrições ativas (CSV)</a>}</div>
      <section className="card" style={{ marginBottom: 16 }}>
        <div className="kpis"><div className="kpi"><b>{active.length}</b><span>ativas</span></div><div className="kpi"><b>{rows.length - active.length}</b><span>anuladas</span></div></div>
        <p className="muted" style={{ marginBottom: 0 }}>O formulário está no rodapé do site e em /newsletter. Cada inscrição guarda o texto aceite e a data (RGPD).
          O envio faz-se num serviço de email à escolha: o CSV leva o link de anulação de cada pessoa, para pôr em cada envio.</p>
      </section>
      <section className="card">
        <h2>Inscrições</h2>
        {rows.length ? (
          <div className="table-wrap"><table className="t"><thead><tr><th>Email</th><th>Estado</th><th>Consentimento</th><th className="hide-sm">Anulada em</th></tr></thead>
            <tbody>{rows.slice(0, 500).map((r) => (
              <tr key={r.email}><td>{r.email}</td><td>{r.status === "active" ? "ativa" : "anulada"}</td><td>{fmtDateTime(r.consent_at)}</td>
                <td className="hide-sm">{r.unsubscribed_at ? fmtDateTime(r.unsubscribed_at) : ""}</td></tr>))}</tbody></table></div>
        ) : <Empty>Ainda ninguém se inscreveu.</Empty>}
      </section>
    </>
  );
}
