import { plainText } from "@/lib/markdown";
import { latest, site } from "@/lib/public";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export async function GET() {
  const { ctx, pub, baseUrl } = await site();
  const items = await latest(ctx, { limit: 30 });
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>${esc(pub.name)}</title><link>${esc(baseUrl)}/</link><description>${esc(pub.description || pub.tagline)}</description><language>${esc(pub.language)}</language>
${items.map((s) => `<item><title>${esc(s.title)}</title><link>${esc(`${baseUrl}/artigo/${s.slug}`)}</link><guid isPermaLink="true">${esc(`${baseUrl}/artigo/${s.slug}`)}</guid>
<pubDate>${new Date(s.published_at).toUTCString()}</pubDate>${s.author_name ? `<author>${esc(s.author_name)}</author>` : ""}${s.section_name ? `<category>${esc(s.section_name)}</category>` : ""}
<description>${esc(s.summary || s.subtitle || plainText(s.body).slice(0, 280))}</description></item>`).join("\n")}
</channel></rss>`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8", "Cache-Control": "public, max-age=300" } });
}
