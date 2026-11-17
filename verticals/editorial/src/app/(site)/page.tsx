import { Teaser } from "@/components/teaser";
import { latest, site } from "@/lib/public";

export default async function Home() {
  const { ctx, pub, sections } = await site();
  const stories = await latest(ctx, { limit: 40 });
  if (!stories.length) {
    return (
      <section className="article" style={{ textAlign: "center", paddingBlock: 40 }}>
        <h1>{pub.name}</h1>
        <p className="dek">{pub.tagline || pub.description}</p>
        <p className="muted">Ainda não há artigos publicados. Volta em breve.</p>
      </section>
    );
  }
  const [lead, ...rest] = stories;
  const rail = rest.slice(0, 5);
  const bySection = sections.map((sec) => ({ sec, items: stories.filter((s) => s.section_slug === sec.slug).slice(0, 4) })).filter((x) => x.items.length);
  return (
    <>
      <div className="lead-grid">
        <Teaser s={lead!} size="l" />
        <div className="rail"><span className="label">Últimas</span>{rail.map((s) => <Teaser key={s.id} s={s} size="s" />)}</div>
      </div>
      {bySection.map(({ sec, items }) => (
        <section key={sec.id} style={{ "--c": sec.color } as React.CSSProperties}>
          <h2 className="section-title"><a href={`/seccao/${sec.slug}`} style={{ textDecoration: "none" }}>{sec.name}</a></h2>
          <div className="teasers">{items.map((s) => <Teaser key={s.id} s={s} />)}</div>
        </section>
      ))}
    </>
  );
}
