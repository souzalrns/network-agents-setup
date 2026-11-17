import Link from "next/link";
import { fmtDateTime } from "@/lib/format";
import { readingMinutes, renderMarkdown } from "@/lib/markdown";

export interface ArticleViewData {
  title: string; subtitle: string; body: string; kind: string; hero_image_url: string | null; hero_caption: string; hero_credit: string;
  section_name?: string | null; section_slug?: string | null; section_color?: string | null;
  author_name?: string | null; author_slug?: string | null; author_public?: boolean | null;
  published_at?: Date | string | null; updated_label?: string | null;
}

/** Cabeçalho, imagem e texto de um artigo, tal como o site os mostra. A pré-visualização da redacção usa o mesmo. */
export function ArticleView({ a, links = true }: { a: ArticleViewData; links?: boolean }) {
  return (
    <>
      <div style={{ "--c": a.section_color ?? "var(--brand)" } as React.CSSProperties}>
        {a.section_slug && (links ? <Link className="kicker" href={`/seccao/${a.section_slug}`}>{a.section_name}</Link> : <span className="kicker">{a.section_name}</span>)}
        {a.kind === "opinion" && <span className="kicker" style={{ marginLeft: 10 }}>Opinião</span>}
        {a.kind === "sponsored" && <span className="kicker" style={{ marginLeft: 10 }}>Conteúdo patrocinado</span>}
      </div>
      <h1>{a.title}</h1>
      {a.subtitle && <p className="dek">{a.subtitle}</p>}
      <div className="byline">
        {a.author_name && (a.author_public && links ? <Link href={`/autor/${a.author_slug}`}>{a.author_name}</Link> : <span>{a.author_name}</span>)}
        {a.published_at ? <time dateTime={new Date(a.published_at).toISOString()}>{fmtDateTime(a.published_at)}</time> : <span>Ainda não publicado</span>}
        {a.updated_label && <span>{a.updated_label}</span>}
        <span>{readingMinutes(a.body)} min de leitura</span>
      </div>
      {a.kind === "sponsored" && <p className="notice">Este conteúdo é pago por um anunciante. A redação não participou na sua produção.</p>}
      {a.hero_image_url && (
        <figure>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={a.hero_image_url} alt={a.hero_caption || ""} />
          {(a.hero_caption || a.hero_credit) && <figcaption>{a.hero_caption}{a.hero_credit && ` Fotografia: ${a.hero_credit}`}</figcaption>}
        </figure>
      )}
      <div className="prose" dangerouslySetInnerHTML={{ __html: renderMarkdown(a.body) }} />
    </>
  );
}
