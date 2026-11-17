import type { Metadata } from "next";
import { Teaser } from "@/components/teaser";
import { search, site } from "@/lib/public";

export const metadata: Metadata = { title: "Pesquisa", robots: { index: false, follow: true } };

export default async function Pesquisa({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const q = String((await searchParams).q ?? "").slice(0, 200);
  const { ctx } = await site();
  const results = await search(ctx, q);
  return (
    <section>
      <h1 className="section-title" style={{ marginTop: 0 }}>Pesquisa</h1>
      <form action="/pesquisa" className="row" role="search" style={{ maxWidth: 560, marginBottom: 22 }}>
        <label className="sr-only" htmlFor="q">Termos</label>
        <input id="q" name="q" type="search" defaultValue={q} placeholder="O que procuras?" style={{ flex: 1, width: "auto" }} />
        <button className="btn primary" type="submit">Procurar</button>
      </form>
      {q && <p className="muted">{results.length} {results.length === 1 ? "resultado" : "resultados"} para «{q}».</p>}
      <div className="teasers">{results.map((s) => <Teaser key={s.id} s={s} />)}</div>
    </section>
  );
}
