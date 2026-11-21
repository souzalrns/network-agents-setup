import { Empty, Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { canWrite, isDesk } from "@/lib/context";
import { withCtx } from "@/lib/db";
import { fmtDateTime } from "@/lib/format";
import { listMedia } from "@/lib/media";
import { deleteMediaAction, updateMediaAction } from "../../actions";
import { Uploader } from "./uploader";

/** Biblioteca de média: imagens da redação, com legenda e crédito, prontas a usar nas peças. */
export default async function Media({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams;
  const { user, ctx } = await requireUser();
  const items = await withCtx(ctx, (tx) => listMedia(tx));
  return (
    <>
      <div className="nr-head"><div><p className="label">Redação</p><h1>Média</h1></div></div>
      <Flash sp={sp} />
      {canWrite(user.role) && <section className="card" style={{ marginBottom: 16 }}><h2>Carregar</h2><Uploader /></section>}
      <section className="card">
        <h2>Biblioteca <span className="label">{items.length}</span></h2>
        {items.length ? (
          <div className="media-grid">{items.map((m) => (
            <figure key={m.id} className="media-item">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/media/${m.id}`} alt={m.alt} loading="lazy" />
              <figcaption className="meta"><span>{m.width && m.height ? `${m.width}×${m.height}` : ""}</span><span>{Math.round(m.size / 1024)} KB</span><span>{m.uploader ?? ""}</span><span>{fmtDateTime(m.created_at)}</span></figcaption>
              <code className="media-md" title="Cola no texto da peça">{`![${m.alt}](/media/${m.id}${m.credit ? ` "${m.credit}"` : ""})`}</code>
              {!m.credit && <small className="warn-text">Falta o crédito.</small>}
              {canWrite(user.role) && (
                <details><summary>Legenda e crédito</summary>
                  <form action={updateMediaAction} className="stack" style={{ marginTop: 6 }}>
                    <input type="hidden" name="media" value={m.id} />
                    <input name="alt" defaultValue={m.alt} placeholder="Legenda" aria-label="Legenda" />
                    <input name="credit" defaultValue={m.credit} placeholder="Crédito" aria-label="Crédito" />
                    <div className="row"><button className="btn small" type="submit">Guardar</button></div>
                  </form>
                  {(isDesk(user.role) || m.uploader === user.name) && (
                    <form action={deleteMediaAction} style={{ marginTop: 6 }}><input type="hidden" name="media" value={m.id} />
                      <button className="btn small danger" type="submit">Apagar</button></form>
                  )}
                </details>
              )}
            </figure>))}
          </div>
        ) : <Empty>Ainda não há imagens. Carrega fotografias para as usares nas peças com legenda e crédito.</Empty>}
      </section>
    </>
  );
}
