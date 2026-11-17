import Link from "next/link";
import { notFound } from "next/navigation";
import { Empty, Flash, StatePill } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { canWrite, isDesk } from "@/lib/context";
import { withCtx } from "@/lib/db";
import { articleOf, compareArticles, fieldsOfVersion, getVersion } from "@/lib/drafts";
import { fmtDateTime } from "@/lib/format";
import { getStory } from "@/lib/stories";
import { isOwner } from "@/lib/workflow";
import { restoreVersionAction } from "../../../../actions";

const LABEL: Record<string, string> = {
  title: "Título", subtitle: "Subtítulo", summary: "Resumo", body: "Texto", slug: "Endereço", hero_image_url: "Imagem",
  hero_caption: "Legenda", hero_credit: "Crédito", tags: "Etiquetas", seo_title: "Título SEO", meta_description: "Descrição SEO", kind: "Tipo",
};

/** Histórico de versões: quem guardou, quando e porquê; comparação palavra a palavra; restauro como versão nova. */
export default async function Versoes({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<Record<string, string | undefined>> }) {
  const { id } = await params;
  const sp = await searchParams;
  const { user, ctx } = await requireUser();
  if (!/^[0-9a-f-]{36}$/i.test(id)) notFound();
  const data = await withCtx(ctx, async (tx) => {
    const story = await getStory(tx, id);
    if (!story) return null;
    const list = await tx<{ version: number; saved_at: Date; note: string; saved_kind: string; name: string | null; words: number; approved: boolean }[]>`
      select v.version, v.saved_at, v.note, v.saved_kind, m.display_name as name,
        coalesce(array_length(regexp_split_to_array(btrim(v.body), '\\s+'), 1), 0) as words,
        v.version = ${story.approved_version ?? -1} as approved
      from story_versions v left join memberships m on m.user_id = v.saved_by and m.publication_id = v.publication_id
      where v.story_id = ${id} order by v.version desc`;
    const b = Number(sp.b) || story.version;
    const a = Number(sp.a) || Math.max(1, b - 1);
    return { story, list, a, b, va: await getVersion(tx, id, a), vb: await getVersion(tx, id, b) };
  });
  if (!data) notFound();
  const { story: s, list, a, b, va, vb } = data;
  const canRestore = canWrite(user.role) && s.state !== "archived"
    && (isDesk(user.role) || (isOwner(user.userId, { assigneeId: s.assignee_id, authorId: s.author_id, createdBy: s.created_by })
        && !["approved", "scheduled", "published"].includes(s.state)));
  const diff = va && vb ? compareArticles(fieldsOfVersion(va, articleOf(s)), fieldsOfVersion(vb, articleOf(s))) : [];
  const changed = diff.filter((d) => d.changed);
  return (
    <>
      <div className="nr-head"><div style={{ minWidth: 0 }}>
        <p className="label"><Link href={`/redacao/pecas/${s.id}`}>{s.title}</Link></p>
        <h1>Versões</h1>
        <div className="meta"><StatePill state={s.state} /><span>Versão actual: {s.version}</span></div>
      </div></div>
      <Flash sp={sp as Record<string, string>} />
      <div className="story-layout">
        <section className="card">
          <form className="row" method="get">
            <label className="field" style={{ flex: "1 1 140px" }}><span>De</span>
              <select name="a" defaultValue={a}>{list.map((v) => <option key={v.version} value={v.version}>v{v.version}</option>)}</select></label>
            <label className="field" style={{ flex: "1 1 140px" }}><span>Para</span>
              <select name="b" defaultValue={b}>{list.map((v) => <option key={v.version} value={v.version}>v{v.version}</option>)}</select></label>
            <button className="btn" type="submit" style={{ alignSelf: "flex-end" }}>Comparar</button>
          </form>
          <h2 style={{ marginTop: 16 }}>v{a} → v{b} <span className="label">{changed.length ? `${changed.length} campos mudaram` : "sem diferenças"}</span></h2>
          {!va?.snapshot && <p className="meta">As versões anteriores à revisão técnica só guardavam título, subtítulo, resumo e texto.</p>}
          <div className="stack">{changed.length ? changed.map((d) => (
            <div key={d.key}>
              <div className="label">{LABEL[d.key]}</div>
              <div className="diff">{d.parts.map((p, i) => p.added ? <ins key={i}>{p.value}</ins> : p.removed ? <del key={i}>{p.value}</del> : <span key={i}>{p.value}</span>)}</div>
            </div>)) : <Empty>As duas versões são iguais.</Empty>}</div>
        </section>
        <aside className="side">
          <section className="card">
            <h2>Todas as versões</h2>
            <ul className="timeline">{list.map((v) => (
              <li key={v.version}>
                <b>v{v.version}</b>{v.version === s.version && <span className="label"> actual</span>}{v.approved && <span className="label"> aprovada</span>}
                {" "}· {v.name ?? v.saved_kind} · <span className="num">{v.words} palavras</span>
                {v.note && <div className="muted">«{v.note}»</div>}
                <div className="meta">{fmtDateTime(v.saved_at)} · <Link href={`?a=${v.version}&b=${s.version}`}>comparar com a actual</Link> · <a href={`/redacao/pre-visualizar/${s.id}?versao=${v.version}`} target="_blank" rel="noreferrer">ver</a></div>
                {canRestore && v.version !== s.version && (
                  <form action={restoreVersionAction} style={{ marginTop: 4 }}>
                    <input type="hidden" name="id" value={s.id} /><input type="hidden" name="version" value={v.version} /><input type="hidden" name="current" value={s.version} />
                    <button className="btn small" type="submit">Restaurar como nova versão</button>
                  </form>
                )}
              </li>))}</ul>
          </section>
        </aside>
      </div>
    </>
  );
}
