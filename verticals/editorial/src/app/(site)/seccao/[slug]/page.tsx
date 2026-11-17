import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Teaser } from "@/components/teaser";
import { latest, site } from "@/lib/public";

type P = { params: Promise<{ slug: string }>; searchParams: Promise<{ pagina?: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  const { sections } = await site();
  const sec = sections.find((s) => s.slug === slug);
  return sec ? { title: sec.name, description: sec.description || undefined, alternates: { canonical: `/seccao/${slug}` } } : {};
}

export default async function Seccao({ params, searchParams }: P) {
  const { slug } = await params;
  const pageN = Math.max(1, Math.min(200, Number((await searchParams).pagina) || 1));
  const { ctx, sections } = await site();
  const sec = sections.find((s) => s.slug === slug);
  if (!sec) notFound();
  const items = await latest(ctx, { section: slug, limit: 21, offset: (pageN - 1) * 20 });
  return (
    <section style={{ "--c": sec.color } as React.CSSProperties}>
      <h1 className="section-title" style={{ marginTop: 0 }}>{sec.name}</h1>
      {sec.description && <p className="muted" style={{ maxWidth: "65ch" }}>{sec.description}</p>}
      {items.length ? <div className="teasers">{items.slice(0, 20).map((s) => <Teaser key={s.id} s={s} />)}</div> : <p className="muted">Ainda não há artigos nesta editoria.</p>}
      <div className="row" style={{ marginTop: 26 }}>
        {pageN > 1 && <Link className="btn" href={`/seccao/${slug}?pagina=${pageN - 1}`}>← Mais recentes</Link>}
        {items.length > 20 && <Link className="btn" href={`/seccao/${slug}?pagina=${pageN + 1}`}>Mais antigos →</Link>}
      </div>
    </section>
  );
}
