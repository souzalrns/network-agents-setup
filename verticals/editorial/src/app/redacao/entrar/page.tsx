import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Flash } from "@/components/ui";
import { currentUser } from "@/lib/auth";
import { loginAction } from "../actions";

export const metadata: Metadata = { title: "Entrar na redação", robots: { index: false, follow: false } };

export default async function LoginPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  if (await currentUser()) redirect("/redacao");
  const sp = await searchParams;
  return (
    <main className="login">
      <div className="card stack">
        <div>
          <h1 style={{ font: "800 26px var(--display)" }}>Redação</h1>
          <p className="muted" style={{ margin: "4px 0 0" }}>Entra com a conta que a direção te criou.</p>
        </div>
        <Flash sp={sp} />
        <form action={loginAction} className="stack">
          <label className="field"><span>Email</span><input id="email" name="email" type="email" autoComplete="username" required /></label>
          <label className="field"><span>Palavra-passe</span><input id="password" name="password" type="password" autoComplete="current-password" required /></label>
          <button className="btn primary" type="submit">Entrar</button>
        </form>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>Esqueceste a palavra-passe? Pede à direção um link de recuperação (Equipa → a tua ficha).</p>
      </div>
    </main>
  );
}
