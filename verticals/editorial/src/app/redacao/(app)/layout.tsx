import type { Metadata } from "next";
import Link from "next/link";
import { NewsroomNav } from "@/components/nav";
import { requireUser } from "@/lib/auth";
import { isDesk, isLead, ROLE_LABEL } from "@/lib/context";
import { getPublication } from "@/lib/publication";
import { logoutAction } from "../actions";

export const metadata: Metadata = { title: "Redação", robots: { index: false, follow: false } };

export default async function NewsroomLayout({ children }: { children: React.ReactNode }) {
  const { user, ctx } = await requireUser();
  const pub = await getPublication(ctx);
  const items = [
    { href: "/redacao", label: "Painel" },
    { href: "/redacao/pautas", label: "Pautas e peças" },
    { href: "/redacao/calendario", label: "Calendário" },
    { href: "/redacao/radar", label: "Radar" },
    { href: "/redacao/fontes", label: "Fontes" },
    ...(isDesk(user.role) ? [{ href: "/redacao/distribuicao", label: "Distribuição" }] : []),
    { href: "/redacao/equipa", label: "Equipa" },
    ...(isLead(user.role) ? [{ href: "/redacao/configuracao", label: "Configuração" }] : []),
  ];
  const [first, ...rest] = pub.name.split(" ");
  return (
    <div style={{ "--brand": pub.primary_color, "--accent": pub.secondary_color } as React.CSSProperties}>
      <header className="nr-top">
        <div className="wrap">
          <Link href="/redacao" className="nr-brand">
            {rest.length ? <><b>{first}</b>{rest.join(" ")}</> : <b>{pub.name}</b>}
          </Link>
          <NewsroomNav items={items} />
          <div className="nr-user">
            <Link href="/redacao/conta" style={{ textDecoration: "none" }}>{user.name} · {ROLE_LABEL[user.role]}</Link>
            <form action={logoutAction}><button className="btn link" type="submit">Sair</button></form>
          </div>
        </div>
      </header>
      <main className="wrap nr-main">{children}</main>
    </div>
  );
}
