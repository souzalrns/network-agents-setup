import { Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { ROLE_LABEL } from "@/lib/context";
import { changePasswordAction } from "../../actions";

export default async function Conta({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { user } = await requireUser();
  const sp = await searchParams;
  return (
    <>
      <div className="nr-head"><div><p className="label">Conta</p><h1>{user.name}</h1></div></div>
      <Flash sp={sp} />
      <section className="card" style={{ maxWidth: 520 }}>
        <p className="meta" style={{ marginTop: 0 }}><span>{user.email}</span><span>{ROLE_LABEL[user.role]}</span></p>
        <h2>Mudar palavra-passe</h2>
        <form action={changePasswordAction} className="stack">
          <label className="field"><span>Nova palavra-passe</span><input id="pw" name="password" type="password" minLength={10} required autoComplete="new-password" /></label>
          <label className="field"><span>Repetir</span><input id="pw2" name="confirm" type="password" minLength={10} required autoComplete="new-password" /></label>
          <div><button className="btn primary" type="submit">Mudar</button></div>
        </form>
      </section>
    </>
  );
}
