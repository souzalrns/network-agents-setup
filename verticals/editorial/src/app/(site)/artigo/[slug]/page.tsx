import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArticleView } from "@/components/article-view";
import { Teaser } from "@/components/teaser";
import { fmtDateTime } from "@/lib/format";
import { plainText } from "@/lib/markdown";
import { article, site } from "@/lib/public";

type P = { params: Promise<{ slug: string }> };

const describe = (s: { meta_description: string; summary: string; subtitle: string; body: string }) =>
  (s.meta_description || s.summary || s.subtitle || plainText(s.body)).slice(0, 160);

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  const { ctx } = await site();
  const a = await article(ctx, slug);
  if (!a) return {};
  const s = a.story;
  return {
    title: s.seo_title || s.title,
    description: describe(s),
    alternates: { canonical: `/artigo/${s.slug}` },
    openGraph: {
      type: "article", title: s.title, description: describe(s), url: `/artigo/${s.slug}`,
      publishedTime: new Date(s.published_at).toISOString(), modifiedTime: new Date(s.updated_at).toISOString(),
      section: s.section_name ?? undefined, tags: s.tags, authors: s.author_name ? [s.author_name] : undefined,
      images: s.hero_image_url ? [{ url: s.hero_image_url, alt: s.hero_caption || s.title }] : undefined,
    },
    twitter: { card: s.hero_image_url ? "summary_large_image" : "summary", title: s.title, description: describe(s) },
  };
}

export default async function Artigo({ params }: P) {
  const { slug } = await params;
  const { ctx, pub, baseUrl } = await site();
  const a = await article(ctx, slug);
  if (!a) notFound();
  const s = a.story;
  const url = `${baseUrl}/artigo/${s.slug}`;
  const updated = new Date(s.updated_at).getTime() - new Date(s.published_at).getTime() > 60_000;
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": s.kind === "opinion" ? "OpinionNewsArticle" : "NewsArticle",
    headline: s.title.slice(0, 110), description: describe(s), mainEntityOfPage: url, url,
    datePublished: new Date(s.published_at).toISOString(), dateModified: new Date(s.updated_at).toISOString(),
    articleSection: s.section_name ?? undefined, keywords: s.tags.join(", ") || undefined, inLanguage: pub.language,
    image: s.hero_image_url ? [s.hero_image_url.startsWith("/") ? `${baseUrl}${s.hero_image_url}` : s.hero_image_url] : undefined,
    author: s.author_name ? [{ "@type": "Person", name: s.author_name, url: s.author_public ? `${baseUrl}/autor/${s.author_slug}` : undefined }] : undefined,
    publisher: { "@type": "NewsMediaOrganization", name: pub.name, url: baseUrl, logo: pub.logo_url ? { "@type": "ImageObject", url: pub.logo_url } : undefined },
  };
  const share = [
    ["WhatsApp", `https://wa.me/?text=${encodeURIComponent(`${s.title} ${url}`)}`],
    ["Facebook", `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`],
    ["X", `https://x.com/intent/post?url=${encodeURIComponent(url)}&text=${encodeURIComponent(s.title)}`],
    ["LinkedIn", `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`],
  ];
  return (
    <article className="article">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
      <ArticleView a={{ ...s, updated_label: updated ? `Atualizado ${fmtDateTime(s.updated_at)}` : null }} />
      {a.refs.length > 0 && (
        <section className="notice"><b>Documentos e dados citados</b>
          <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>{a.refs.map((r) => <li key={r.url}><a href={r.url} rel="noopener noreferrer">{r.title || r.url}</a></li>)}</ul></section>
      )}
      {a.corrections.length > 0 && (
        <section className="notice" id="correcoes"><b>Correções</b>
          {a.corrections.map((c, i) => <p key={i} style={{ margin: "6px 0 0" }}><span className="muted">{fmtDateTime(c.created_at)}:</span> {c.text}</p>)}</section>
      )}
      <div className="share" aria-label="Partilhar">{share.map(([n, href]) => <a key={n} className="btn small" href={href} rel="noopener noreferrer" target="_blank">{n}</a>)}</div>
      <p className="muted" style={{ fontSize: 14, marginTop: 18 }}>Encontraste um erro? Escreve-nos{pub.contact_email ? ` para ${pub.contact_email}` : ""}. Consulta a <Link href="/pagina/politica-de-correcoes">política de correções</Link>.</p>
      {a.related.length > 0 && (
        <section style={{ marginTop: 34 }}><h2 className="section-title" style={{ fontSize: 22 }}>Na mesma editoria</h2>
          <div className="teasers">{a.related.map((r) => <Teaser key={r.id} s={r} />)}</div></section>
      )}
    </article>
  );
}
