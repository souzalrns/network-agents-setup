import Link from "next/link";
import { fmtDate } from "@/lib/format";
import type { PublicStory } from "@/lib/public";

export function Teaser({ s, size = "m", image = true }: { s: PublicStory; size?: "l" | "m" | "s"; image?: boolean }) {
  const H = size === "l" ? "h2" : "h3";
  return (
    <article className="teaser" style={{ "--c": s.section_color ?? "var(--brand)" } as React.CSSProperties}>
      {image && s.hero_image_url && size !== "s" && (
        // eslint-disable-next-line @next/next/no-img-element
        <Link href={`/artigo/${s.slug}`} tabIndex={-1}><img src={s.hero_image_url} alt="" loading="lazy" /></Link>
      )}
      {s.section_slug && <Link className="kicker" href={`/seccao/${s.section_slug}`}>{s.kind === "opinion" ? "Opinião" : s.section_name}</Link>}
      <H><Link className="t" href={`/artigo/${s.slug}`}>{s.title}</Link></H>
      {size !== "s" && (s.subtitle || s.summary) && <p>{s.subtitle || s.summary}</p>}
      <div className="meta">{s.author_name && <span>{s.author_name}</span>}<time dateTime={new Date(s.published_at).toISOString()}>{fmtDate(s.published_at)}</time></div>
    </article>
  );
}
