import Link from "next/link";

export default function NotFound() {
  return (
    <section className="article" style={{ paddingBlock: 30 }}>
      <h1>Página não encontrada</h1>
      <p className="dek">O endereço pode estar errado, ou o artigo foi retirado.</p>
      <p><Link className="btn primary" href="/">Ir para a página inicial</Link> <Link className="btn" href="/pesquisa">Pesquisar</Link></p>
    </section>
  );
}
