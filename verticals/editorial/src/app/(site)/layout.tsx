import type { Metadata } from "next";
import Link from "next/link";
import { publishedPages, site } from "@/lib/public";

export async function generateMetadata(): Promise<Metadata> {
  const { pub, baseUrl } = await site();
  return {
    metadataBase: new URL(baseUrl),
    title: { default: pub.tagline ? `${pub.name} · ${pub.tagline}` : pub.name, template: `%s · ${pub.name}` },
    description: pub.description || pub.tagline,
    icons: pub.favicon_url ? { icon: pub.favicon_url } : undefined,
    alternates: { types: { "application/rss+xml": `${baseUrl}/feed.xml` } },
    openGraph: { siteName: pub.name, locale: pub.language.replace("-", "_"), type: "website" },
    robots: pub.public_launch ? { index: true, follow: true } : { index: false, follow: false },
  };
}

export default async function SiteLayout({ children }: { children: React.ReactNode }) {
  const { pub, sections, ctx } = await site();
  const pages = await publishedPages(ctx);
  const [first, ...rest] = pub.name.split(" ");
  const social = Object.entries(pub.social_links ?? {});
  return (
    <div style={{ "--brand": pub.primary_color, "--accent": pub.secondary_color } as React.CSSProperties}>
      <a href="#conteudo" className="sr-only">Saltar para o conteúdo</a>
      {!pub.public_launch && <div className="prelaunch">Edição de pré-lançamento: este site ainda não está aberto ao público.</div>}
      <header className="site-top">
        <div className="wrap">
          <Link href="/" className="masthead">
            {pub.logo_url
              // eslint-disable-next-line @next/next/no-img-element
              ? <img src={pub.logo_url} alt={pub.name} style={{ height: 52, width: "auto" }} />
              : <span className="name">{rest.length ? <><i>{first}</i>{rest.join(" ")}</> : <i>{pub.name}</i>}</span>}
            {pub.tagline && <span className="tag">{pub.tagline}</span>}
          </Link>
          <form action="/pesquisa" className="search-inline" role="search">
            <label className="sr-only" htmlFor="q-top">Pesquisar</label>
            <input id="q-top" name="q" type="search" placeholder="Pesquisar" />
            <button className="btn small" type="submit">Procurar</button>
          </form>
        </div>
      </header>
      <nav className="site-nav" aria-label="Editorias">
        <div className="wrap">
          <Link href="/">Últimas</Link>
          {sections.map((s) => <Link key={s.id} href={`/seccao/${s.slug}`}>{s.name}</Link>)}
        </div>
      </nav>
      <main id="conteudo" className="wrap site-main">{children}</main>
      <footer className="site-foot">
        <div className="wrap cols">
          <div>
            <b>{pub.name}</b>
            {pub.description && <p className="muted" style={{ marginTop: 6 }}>{pub.description}</p>}
            {pub.contact_email && <p>Redação: {pub.contact_email}</p>}
          </div>
          <div>
            <b>Sobre</b>
            <ul style={{ listStyle: "none", padding: 0, margin: "6px 0 0" }}>
              {pages.map((p) => <li key={p.slug}><Link href={`/pagina/${p.slug}`}>{p.title}</Link></li>)}
              <li><a href="/feed.xml">RSS</a></li>
            </ul>
          </div>
          <div>
            <b>Ficha técnica</b>
            <ul style={{ listStyle: "none", padding: 0, margin: "6px 0 0" }} className="muted">
              {pub.legal?.director && <li>Direção: {pub.legal.director}</li>}
              {pub.legal?.owner && <li>Propriedade: {pub.legal.owner}</li>}
              {pub.legal?.registration && <li>Registo ERC: {pub.legal.registration}</li>}
              {pub.legal?.address && <li>{pub.legal.address}</li>}
            </ul>
          </div>
          {social.length > 0 && (
            <div><b>Segue-nos</b>
              <ul style={{ listStyle: "none", padding: 0, margin: "6px 0 0" }}>{social.map(([k, url]) => <li key={k}><a href={url} rel="noopener noreferrer me">{k}</a></li>)}</ul>
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}
