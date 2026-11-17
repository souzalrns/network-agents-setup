import Link from "next/link";
import { Empty, Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { OUTPUT_KIND_LABEL } from "@/lib/constants";
import { canWrite, isDesk } from "@/lib/context";
import { withCtx } from "@/lib/db";
import { relTime } from "@/lib/format";
import { agentName, getPublication } from "@/lib/publication";
import { reviewOutputAction } from "../../actions";
import { addFeedAction, dismissAction, promoteAction, runNowAction, toggleFeedAction } from "./actions";
import { suggestAction } from "./suggest-action";

const STATUS_LABEL: Record<string, string> = { never: "Nunca lida", ok: "OK", not_modified: "Sem novidades", error: "Erro", blocked: "Bloqueada" };

export default async function Radar({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { user, ctx } = await requireUser();
  const sp = await searchParams;
  const pub = await getPublication(ctx);
  const { items, sources, outputs } = await withCtx(ctx, async (tx) => ({
    items: await tx<{ id: string; title: string; url: string; excerpt: string; published_at: Date | null; fetched_at: Date; relevance: number; topics: string[]; source: string; tier: string; dups: number }[]>`
      select i.id, i.title, i.url, i.excerpt, i.published_at, i.fetched_at, i.relevance, i.topics, f.name as source, f.tier,
        (select count(*)::int from feed_items d where d.duplicate_of = i.id) as dups
      from feed_items i join feed_sources f on f.id = i.feed_source_id
      where i.status = 'new' and i.duplicate_of is null
      order by i.relevance desc, i.fetched_at desc limit 80`,
    sources: await tx<{ id: string; name: string; feed_url: string; tier: string; scope: string; active: boolean; last_status: string; last_fetched_at: Date | null; last_error: string }[]>`
      select id, name, feed_url, tier, scope, active, last_status, last_fetched_at, last_error from feed_sources order by name`,
    outputs: await tx<{ id: string; agent_id: string; kind: string; payload: { clusters?: { title?: string; why?: string; urls?: string[]; item_urls?: string[]; sources_count?: number; suggested_section?: string }[] }; created_at: Date }[]>`
      select id, agent_id, kind, payload, created_at from agent_outputs where kind = 'story_suggestions' and status = 'proposed'
      order by created_at desc limit 3`,
  }));
  const writer = canWrite(user.role);
  return (
    <>
      <div className="nr-head">
        <div><p className="label">Monitorização de fontes</p><h1>{agentName(pub, "editorial.radar")}</h1></div>
        <div className="row">
          {isDesk(user.role) && <form action={runNowAction}><button className="btn" type="submit">Ler fontes agora</button></form>}
          {writer && <form action={suggestAction}><button className="btn primary" type="submit">Pedir sugestões de pautas</button></form>}
        </div>
      </div>
      <Flash sp={sp} />
      <p className="muted" style={{ marginTop: 0, maxWidth: "75ch" }}>
        O radar lê feeds públicos e guarda só título, um excerto curto e a ligação: nunca o artigo inteiro.
        Nada aqui é notícia confirmada. Uma entrada só vira ideia quando alguém da redação decide.
      </p>

      {outputs.length > 0 && (
        <section className="card" id="propostas" style={{ marginBottom: 14 }}>
          <h2>Sugestões de pautas <span className="label">por rever</span></h2>
          {outputs.map((o) => (
            <div key={o.id} className="stack" style={{ gap: 8 }}>
              <div className="meta">{agentName(pub, o.agent_id)} · {OUTPUT_KIND_LABEL[o.kind]} · {relTime(o.created_at)}</div>
              <div className="list">{(o.payload.clusters ?? []).map((c, i) => (
                <div key={i}><b>{c.title}</b>{c.why && <div className="muted" style={{ fontSize: 14 }}>{c.why}</div>}
                  <div className="meta">{c.sources_count != null && <span>{c.sources_count} fontes</span>}{c.suggested_section && <span>{c.suggested_section}</span>}
                    {(c.item_urls ?? c.urls ?? []).slice(0, 3).map((u) => <a key={u} href={u} target="_blank" rel="noreferrer">{new URL(u).hostname}</a>)}</div></div>))}</div>
              {writer && (
                <div className="row">
                  {(["accepted", "dismissed"] as const).map((st) => (
                    <form key={st} action={reviewOutputAction}><input type="hidden" name="output" value={o.id} /><input type="hidden" name="status" value={st} />
                      <input type="hidden" name="back" value="/redacao/radar" /><button className="btn small" type="submit">{st === "accepted" ? "Aproveitar" : "Descartar"}</button></form>))}
                </div>
              )}
            </div>
          ))}
        </section>
      )}

      <section className="card">
        <h2>Entradas novas <span className="label">{items.length}</span></h2>
        <div className="list">{items.length ? items.map((i) => (
          <div key={i.id} className="stack" style={{ gap: 4 }}>
            <a className="item-title" href={i.url} target="_blank" rel="noreferrer">{i.title}</a>
            {i.excerpt && <div className="muted" style={{ fontSize: 14 }}>{i.excerpt}</div>}
            <div className="meta"><span>{i.source}</span><span className="num">Relevância {i.relevance}</span>{i.topics.length > 0 && <span>{i.topics.join(", ")}</span>}
              {i.dups > 0 && <span>também em {i.dups} {i.dups === 1 ? "outra fonte" : "outras fontes"}</span>}<span>{relTime(i.published_at ?? i.fetched_at)}</span></div>
            {writer && (
              <div className="row">
                <form action={promoteAction}><input type="hidden" name="item" value={i.id} /><button className="btn small" type="submit">Criar ideia</button></form>
                <form action={dismissAction}><input type="hidden" name="item" value={i.id} /><button className="btn small link" type="submit">Descartar</button></form>
              </div>
            )}
          </div>)) : <Empty>Sem entradas novas. {sources.length ? "Lê as fontes ou espera pela próxima leitura automática." : "Acrescenta fontes abaixo."}</Empty>}</div>
      </section>

      <section className="card table-wrap" style={{ marginTop: 14 }}>
        <h2>Fontes do radar <span className="label">{sources.length}</span></h2>
        {sources.length ? (
          <table className="t"><thead><tr><th>Fonte</th><th>Tipo</th><th>Estado</th><th>Última leitura</th><th></th></tr></thead>
            <tbody>{sources.map((s) => (
              <tr key={s.id} style={{ opacity: s.active ? 1 : 0.55 }}>
                <td><b>{s.name}</b><div className="meta" style={{ overflowWrap: "anywhere" }}>{s.feed_url}</div></td>
                <td>{s.tier} · {s.scope}</td>
                <td>{STATUS_LABEL[s.last_status] ?? s.last_status}{s.last_error && <div className="meta">{s.last_error.slice(0, 120)}</div>}</td>
                <td>{s.last_fetched_at ? relTime(s.last_fetched_at) : "—"}</td>
                <td>{isDesk(user.role) && <form action={toggleFeedAction}><input type="hidden" name="source" value={s.id} /><button className="btn small" type="submit">{s.active ? "Desligar" : "Ligar"}</button></form>}</td>
              </tr>))}</tbody></table>
        ) : <Empty>Ainda não há fontes. As fontes primárias e institucionais (INE, Diário da República, câmara, universidade) devem vir primeiro.</Empty>}
        {isDesk(user.role) && (
          <form action={addFeedAction} className="row" style={{ marginTop: 12 }}>
            <input name="name" placeholder="Nome" aria-label="Nome da fonte" required style={{ flex: "1 1 160px", width: "auto" }} />
            <input name="feed_url" type="url" placeholder="https://…/feed" aria-label="Endereço do feed" required style={{ flex: "2 1 240px", width: "auto" }} />
            <select name="tier" aria-label="Tipo" style={{ width: "auto" }}><option value="primary">Primária</option><option value="institutional">Institucional</option><option value="media">Comunicação social</option></select>
            <select name="scope" aria-label="Âmbito" style={{ width: "auto" }}><option value="local">Local</option><option value="national">Nacional</option><option value="international">Internacional</option></select>
            <input name="interval_minutes" type="number" min={15} max={10080} defaultValue={60} aria-label="Minutos entre leituras" style={{ width: 90 }} />
            <button className="btn" type="submit">Acrescentar</button>
          </form>
        )}
        <p className="muted" style={{ fontSize: 13 }}>Só se lêem domínios da lista autorizada (<code>config/radar-allowlist.json</code>). <Link href="/redacao/configuracao">Configuração</Link></p>
      </section>
    </>
  );
}
