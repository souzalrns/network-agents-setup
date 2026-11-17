import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArticleView } from "@/components/article-view";
import { requireUser } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { articleOf, fieldsOfVersion, getDraft, getVersion } from "@/lib/drafts";
import { fmtDateTime } from "@/lib/format";
import { getPublication } from "@/lib/publication";
import { listSections, listTeam } from "@/lib/queries";
import { getStory } from "@/lib/stories";
import { STATE_LABEL } from "@/lib/workflow";

export const metadata: Metadata = { title: "Pré-visualização", robots: { index: false, follow: false } };

/**
 * Pré-visualização fiel: o artigo com o mesmo componente e as mesmas folhas de estilo do site.
 * Mostra o rascunho por guardar (se houver), a versão actual, ou uma versão antiga (?versao=N).
 */
export default async function Previsualizar({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<Record<string, string | undefined>> }) {
  const { id } = await params;
  const sp = await searchParams;
  const { ctx } = await requireUser();
  if (!/^[0-9a-f-]{36}$/i.test(id)) notFound();
  const data = await withCtx(ctx, async (tx) => {
    const story = await getStory(tx, id);
    if (!story) return null;
    const wanted = Number(sp.versao);
    const version = Number.isInteger(wanted) && wanted > 0 ? await getVersion(tx, id, wanted) : null;
    const draft = version || sp.fonte === "guardada" ? null : await getDraft(tx, id);
    return { story, version, draft, sections: await listSections(tx), team: await listTeam(tx) };
  });
  if (!data) notFound();
  const pub = await getPublication(ctx);
  const { story, version, draft } = data;
  const fields = version ? fieldsOfVersion(version, articleOf(story)) : draft ? draft.fields : articleOf(story);
  const sec = data.sections.find((x) => x.id === story.section_id);
  const author = data.team.find((m) => m.user_id === story.author_id);
  const origin = version ? `versão ${version.version} (${fmtDateTime(version.saved_at)})`
    : draft ? `rascunho por guardar de ${draft.by_name ?? "alguém"} (${fmtDateTime(draft.updated_at)})` : `versão ${story.version}, guardada`;
  return (
    <div style={{ "--brand": pub.primary_color, "--accent": pub.secondary_color } as React.CSSProperties}>
      <div className="preview-bar">
        <div className="wrap row" style={{ justifyContent: "space-between" }}>
          <span><b>Pré-visualização</b> · {STATE_LABEL[story.state]} · {origin}</span>
          <span className="row">
            {draft && <Link href={`?fonte=guardada`}>Ver a versão guardada</Link>}
            <Link className="btn small" href={`/redacao/pecas/${story.id}#artigo`}>Voltar à peça</Link>
          </span>
        </div>
      </div>
      <main className="wrap" style={{ paddingBlock: 24 }}>
        <article className="article">
          <ArticleView links={false} a={{ ...fields, section_name: sec?.name ?? null, section_slug: sec?.slug ?? null, section_color: sec?.color ?? null,
            author_name: author?.name ?? null, author_slug: author?.author_slug ?? null, author_public: author?.public_profile ?? false,
            published_at: story.published_at }} />
        </article>
      </main>
    </div>
  );
}
