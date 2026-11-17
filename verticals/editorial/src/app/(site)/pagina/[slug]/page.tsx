import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { renderMarkdown } from "@/lib/markdown";
import { page, site } from "@/lib/public";

type P = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const p = await page((await site()).ctx, (await params).slug);
  return p ? { title: p.title } : {};
}

export default async function Pagina({ params }: P) {
  const { ctx } = await site();
  const p = await page(ctx, (await params).slug);
  if (!p) notFound();
  return (
    <article className="article">
      <h1>{p.title}</h1>
      <div className="prose" dangerouslySetInnerHTML={{ __html: renderMarkdown(p.body) }} />
    </article>
  );
}
