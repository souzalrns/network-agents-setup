import { Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { isLead, ROLE_LABEL, ROLES } from "@/lib/context";
import { withCtx } from "@/lib/db";
import { listTeam } from "@/lib/queries";
import { addMemberAction, removeMemberAction, updateMemberAction } from "../../actions";

const ROLE_HELP: Record<string, string> = {
  admin: "Tudo, incluindo papéis de administração.", director: "Linha editorial, equipa, configuração, aprovação e publicação.",
  editor: "Aprova pautas e artigos, agenda e publica.", journalist: "Propõe pautas, investiga e escreve as suas peças.",
  contributor: "Como jornalista, para colaborações pontuais.", reviewer: "Lê e comenta; não altera peças.",
};

export default async function Equipa({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { user, ctx } = await requireUser();
  const sp = await searchParams;
  const team = await withCtx(ctx, (tx) => listTeam(tx));
  const lead = isLead(user.role);
  return (
    <>
      <div className="nr-head"><div><p className="label">Redação</p><h1>Equipa</h1></div></div>
      <Flash sp={sp} />
      <div className="cards">
        {team.map((m) => {
          const canEdit = lead || m.user_id === user.userId;
          return (
            <section key={m.user_id} className="card">
              <form action={updateMemberAction} className="stack">
                <input type="hidden" name="user" value={m.user_id} />
                <fieldset disabled={!canEdit} style={{ border: 0, padding: 0, margin: 0 }} className="stack">
                  <label className="field"><span>Nome</span><input name="name" defaultValue={m.name} /></label>
                  <div className="meta"><span>{m.email}</span><span>/autor/{m.author_slug}</span></div>
                  <label className="field"><span>Papel</span>
                    <select name="role" defaultValue={m.role} disabled={!lead || m.user_id === user.userId}>{ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}</select>
                    <small>{ROLE_HELP[m.role]}</small></label>
                  <label className="field"><span>Biografia pública</span><textarea name="bio" defaultValue={m.bio} style={{ minHeight: 60 }} /></label>
                  <label className="check"><input type="checkbox" name="public_profile" value="1" defaultChecked={m.public_profile} /> Página de autor pública</label>
                  {canEdit && <div className="row"><button className="btn small" type="submit">Guardar</button></div>}
                </fieldset>
              </form>
              {lead && m.user_id !== user.userId && (
                <form action={removeMemberAction} style={{ marginTop: 8 }}><input type="hidden" name="user" value={m.user_id} />
                  <button className="btn small danger" type="submit">Retirar acesso</button></form>
              )}
            </section>
          );
        })}
      </div>
      {lead && (
        <section className="card" style={{ marginTop: 16, maxWidth: 760 }}>
          <h2>Acrescentar pessoa</h2>
          <form action={addMemberAction} className="stack">
            <div className="grid2">
              <label className="field"><span>Nome</span><input id="m-name" name="name" required /></label>
              <label className="field"><span>Email</span><input id="m-email" name="email" type="email" required /></label>
              <label className="field"><span>Papel</span><select id="m-role" name="role" defaultValue="journalist">{ROLES.filter((r) => r !== "admin" || user.role === "admin").map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}</select></label>
              <label className="field"><span>Palavra-passe inicial</span><input id="m-pass" name="password" type="password" minLength={10} required autoComplete="new-password" /><small>A pessoa muda-a em «Conta».</small></label>
            </div>
            <div><button className="btn primary" type="submit">Acrescentar à equipa</button></div>
          </form>
        </section>
      )}
    </>
  );
}
