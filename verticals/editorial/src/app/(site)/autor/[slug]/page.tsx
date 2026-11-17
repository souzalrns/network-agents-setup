import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Teaser } from "@/components/teaser";
import { author, latest, site } from "@/lib/public";

type P = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  const a = await author((await site()).ctx, slug);
  return a ? { title: a.name, description: a.bio.slice(0, 160) || undefined } : {};
}

export default async function Autor({ params }: P) {
  const { slug } = await params;
  const { ctx } = await site();
  const a = await author(ctx, slug);
  if (!a) notFound();
  const items = await latest(ctx, { author: slug, limit: 30 });
  return (
    <section>
      <h1 className="section-title" style={{ marginTop: 0 }}>{a.name}</h1>
      {a.bio && <p style={{ maxWidth: "65ch" }}>{a.bio}</p>}
      {items.length ? <div className="teasers">{items.map((s) => <Teaser key={s.id} s={s} />)}</div> : <p className="muted">Ainda sem artigos publicados.</p>}
    </section>
  );
}
