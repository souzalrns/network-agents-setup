import Link from "next/link";
import { Empty, Flash } from "@/components/ui";
import { requireDesk } from "@/lib/auth";
import { CHANNEL_LABEL, DIST_STATE_LABEL } from "@/lib/constants";
import { withCtx } from "@/lib/db";
import { relTime } from "@/lib/format";
import { httpTransport } from "@/lib/postiz";
import { distributionStateAction } from "../../actions";
import { dispatchAction } from "./actions";

export default async function Distribuicao({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { ctx } = await requireDesk();
  const sp = await searchParams;
  const rows = await withCtx(ctx, (tx) => tx<{ id: string; story_id: string; title: string; channel: string; state: string; content: Record<string, unknown>; prepared_label: string; updated_at: Date; external_ref: string }[]>`
    select d.id, d.story_id, s.title, d.channel, d.state, d.content, d.prepared_label, d.updated_at, d.external_ref
    from distribution_items d join stories s on s.id = d.story_id where d.state <> 'discarded' order by d.updated_at desc limit 200`);
  const configured = httpTransport() !== null;
  const approved = rows.filter((r) => r.state === "approved").length;
  return (
    <>
      <div className="nr-head">
        <div><p className="label">Redes e canais</p><h1>Distribuição</h1></div>
        <form action={dispatchAction}><button className="btn primary" type="submit" disabled={!approved}>Enviar {approved} aprovados para o Postiz (rascunho)</button></form>
      </div>
      <Flash sp={sp} />
      <p className="muted" style={{ marginTop: 0, maxWidth: "75ch" }}>
        O site é a fonte principal; aqui ficam as adaptações para Instagram, YouTube, podcast e newsletter. Só seguem para o agendador
        conteúdos aprovados por uma pessoa da edição, e entram no Postiz como <b>rascunho</b>: a decisão de agendar continua a ser humana.
        {!configured && " O Postiz ainda não está ligado (faltam POSTIZ_API_URL e POSTIZ_API_KEY): o envio só simula."}
      </p>
      <section className="card table-wrap">
        {rows.length ? (
          <table className="t"><thead><tr><th>Peça</th><th>Canal</th><th>Texto</th><th>Estado</th><th></th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.id}>
                <td><Link href={`/redacao/pecas/${r.story_id}#distribuicao`}>{r.title}</Link><div className="meta">{relTime(r.updated_at)}{r.prepared_label && ` · ${r.prepared_label}`}</div></td>
                <td>{CHANNEL_LABEL[r.channel]}</td>
                <td style={{ maxWidth: 360, whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{String(r.content.text ?? "").slice(0, 220)}</td>
                <td>{DIST_STATE_LABEL[r.state]}{r.external_ref && <div className="meta">{r.external_ref.split(" ").pop()}</div>}</td>
                <td>{["draft", "in_review"].includes(r.state) && (
                  <form action={distributionStateAction}><input type="hidden" name="item" value={r.id} /><input type="hidden" name="id" value={r.story_id} />
                    <input type="hidden" name="back" value="/redacao/distribuicao" /><button className="btn small primary" name="state" value="approved" type="submit">Aprovar</button></form>)}</td>
              </tr>))}</tbody></table>
        ) : <Empty>Ainda não há adaptações. Criam-se na ficha de cada peça aprovada, ou pedindo ao agente de edição.</Empty>}
      </section>
    </>
  );
}
