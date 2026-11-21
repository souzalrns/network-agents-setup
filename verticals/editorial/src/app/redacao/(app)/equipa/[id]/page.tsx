import Link from "next/link";
import { notFound } from "next/navigation";
import { Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { isLead, ROLE_LABEL, ROLES } from "@/lib/context";
import { withCtx } from "@/lib/db";
import { listTeam } from "@/lib/queries";
import { removeMemberAction, updateMemberAction } from "../../../actions";
import { ResetLink } from "./reset-link";

const ROLE_HELP: Record<string, string> = {
  admin: "Tudo, incluindo papéis de administração.", director: "Linha editorial, equipa, configuração, aprovação e publicação.",
  editor: "Aprova pautas e artigos, agenda e publica.", journalist: "Propõe pautas, investiga e escreve as suas peças.",
  contributor: "Como jornalista, para colaborações pontuais.", reviewer: "Lê, comenta e verifica afirmações; não altera peças.",
};

/** Ficha de uma pessoa: um formulário de cada vez, em vez de um por pessoa na lista. */
export default async function Ficha({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { id } = await params;
  const sp = await searchParams;
  const { user, ctx } = await requireUser();
  const lead = isLead(user.role);
  if (!/^[0-9a-f-]{36}$/i.test(id) || (!lead && id !== user.userId)) notFound();
  const m = (await withCtx(ctx, (tx) => listTeam(tx))).find((x) => x.user_id === id);
  if (!m) notFound();
  const self = m.user_id === user.userId;
  return (
    <>
      <div className="nr-head"><div><p className="label"><Link href="/redacao/equipa">Equipa</Link></p><h1>{m.name}</h1>
        <div className="meta"><span>{ROLE_LABEL[m.role]}</span><span>{m.email}</span></div></div></div>
      <Flash sp={sp} />
      <section className="card" style={{ maxWidth: 720 }}>
        <form action={updateMemberAction} className="stack">
          <input type="hidden" name="user" value={m.user_id} />
          <label className="field"><span>Nome</span><input name="name" defaultValue={m.name} /></label>
          <label className="field"><span>Papel</span>
            <select name="role" defaultValue={m.role} disabled={!lead || self}>{ROLES.filter((r) => r !== "admin" || user.role === "admin" || m.role === "admin").map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}</select>
            <small>{self ? "Ninguém altera o próprio papel." : ROLE_HELP[m.role]}</small></label>
          <label className="field"><span>Biografia pública</span><textarea name="bio" defaultValue={m.bio} style={{ minHeight: 90 }} /></label>
          <label className="check"><input type="checkbox" name="public_profile" value="1" defaultChecked={m.public_profile} /> Página de autor pública (/autor/{m.author_slug})</label>
          <div className="row"><button className="btn primary" type="submit">Guardar ficha</button><Link className="btn" href="/redacao/equipa">Voltar</Link></div>
        </form>
      </section>
      {lead && !self && (
        <section className="card" style={{ maxWidth: 720, marginTop: 16 }}>
          <h2>Acesso</h2>
          <p className="muted">Se a pessoa esqueceu a palavra-passe, gera um link de recuperação e entrega-lho.</p>
          <ResetLink userId={m.user_id} name={m.name} />
          <hr style={{ margin: "16px 0", border: 0, borderTop: "1px solid var(--line)" }} />
          <p className="muted">Retirar o acesso não apaga as peças nem o histórico desta pessoa.</p>
          <form action={removeMemberAction}><input type="hidden" name="user" value={m.user_id} />
            <button className="btn danger" type="submit">Retirar acesso a esta publicação</button></form>
        </section>
      )}
    </>
  );
}
