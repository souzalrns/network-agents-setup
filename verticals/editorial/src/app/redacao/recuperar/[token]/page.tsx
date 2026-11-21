import type { Metadata } from "next";
import { Flash } from "@/components/ui";
import { resetPasswordAction } from "../../actions";

export const metadata: Metadata = { title: "Nova palavra-passe", robots: { index: false, follow: false }, referrer: "no-referrer" };

/** Página do link de recuperação gerado pela direção: escolher uma palavra-passe nova (uso único, 24 h). */
export default async function Recuperar({ params, searchParams }: { params: Promise<{ token: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { token } = await params;
  const sp = await searchParams;
  return (
    <main className="login">
      <div className="card stack">
        <div>
          <h1 style={{ font: "800 26px var(--display)" }}>Nova palavra-passe</h1>
          <p className="muted" style={{ margin: "4px 0 0" }}>Este link só funciona uma vez e durante 24 horas.</p>
        </div>
        <Flash sp={sp} />
        <form action={resetPasswordAction} className="stack">
          <input type="hidden" name="token" value={token} />
          <label className="field"><span>Palavra-passe nova</span><input id="password" name="password" type="password" minLength={10} required autoComplete="new-password" /><small>Pelo menos 10 caracteres.</small></label>
          <label className="field"><span>Repetir</span><input id="confirm" name="confirm" type="password" minLength={10} required autoComplete="new-password" /></label>
          <button className="btn primary" type="submit">Guardar e entrar</button>
        </form>
      </div>
    </main>
  );
}
