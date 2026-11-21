import type { Metadata } from "next";
import Link from "next/link";
import { NewsletterForm } from "@/components/newsletter-form";
import { publishedPages, site } from "@/lib/public";

export const metadata: Metadata = { title: "Newsletter" };

export default async function Newsletter({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const { pub, ctx } = await site();
  const privacy = (await publishedPages(ctx)).some((p) => p.slug === "privacidade");
  return (
    <section className="article" style={{ paddingBlock: 30 }}>
      <h1>Newsletter</h1>
      <p className="dek">As notícias de {pub.name} no teu email. Sem publicidade de terceiros e sem partilhar o teu endereço.</p>
      <NewsletterForm pubName={pub.name} status={sp.estado} where="pagina" />
      <p className="muted" style={{ fontSize: 14, marginTop: 18 }}>Guardamos o email, a data e o texto que aceitaste, só para te enviar a newsletter. Podes anular a inscrição a qualquer momento pelo link em cada envio.{privacy && <> Mais na <Link href="/pagina/privacidade">política de privacidade</Link>.</>}</p>
    </section>
  );
}
