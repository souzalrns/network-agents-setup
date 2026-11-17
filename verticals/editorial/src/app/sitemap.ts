import type { MetadataRoute } from "next";
import { latest, publishedPages, site } from "@/lib/public";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { ctx, sections, baseUrl, pub } = await site();
  if (!pub.public_launch) return [];
  const [stories, pages] = await Promise.all([latest(ctx, { limit: 100 }), publishedPages(ctx)]);
  return [
    { url: `${baseUrl}/`, changeFrequency: "hourly", priority: 1 },
    ...sections.map((s) => ({ url: `${baseUrl}/seccao/${s.slug}`, changeFrequency: "daily" as const, priority: 0.7 })),
    ...stories.map((s) => ({ url: `${baseUrl}/artigo/${s.slug}`, lastModified: s.updated_at, priority: 0.8 })),
    ...pages.map((p) => ({ url: `${baseUrl}/pagina/${p.slug}`, lastModified: p.updated_at, priority: 0.3 })),
  ];
}
