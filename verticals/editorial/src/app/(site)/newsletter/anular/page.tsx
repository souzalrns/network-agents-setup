import type { Metadata } from "next";
import { unsubscribe } from "@/lib/newsletter";

export const metadata: Metadata = { title: "Anular inscrição", robots: { index: false, follow: false } };

/** Anular a inscrição pelo link de cada envio. Basta abrir o link; não pede mais nada. */
export default async function Anular({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const { t } = await searchParams;
  const ok = t ? await unsubscribe(t) : false;
  return (
    <section className="article" style={{ paddingBlock: 30 }}>
      <h1>{ok ? "Inscrição anulada" : "Link inválido"}</h1>
      <p className="dek">{ok ? "Não vais receber mais a newsletter. Se mudares de ideias, podes voltar a inscrever-te quando quiseres." : "Este link não corresponde a nenhuma inscrição. Se continuas a receber a newsletter, responde a um envio e tratamos disso."}</p>
    </section>
  );
}
