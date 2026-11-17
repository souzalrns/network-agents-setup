import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { type SessionUser, sessionFromToken } from "./auth-core";
import type { Ctx } from "./context";
import { humanCtx, isDesk, isLead } from "./context";

export const SESSION_COOKIE = "ed_session";

export async function currentUser(): Promise<SessionUser | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  return sessionFromToken(token);
}

/** Sessão obrigatória: sem ela, vai para a entrada. Devolve o utilizador e o contexto da transacção. */
export async function requireUser(): Promise<{ user: SessionUser; ctx: Ctx }> {
  const user = await currentUser();
  if (!user) redirect("/redacao/entrar");
  return { user, ctx: humanCtx(user.publicationId, user.userId, user.role, user.name) };
}

export async function requireDesk() {
  const s = await requireUser();
  if (!isDesk(s.user.role)) redirect("/redacao?erro=" + encodeURIComponent("Esta área é da edição e da direção."));
  return s;
}

export async function requireLead() {
  const s = await requireUser();
  if (!isLead(s.user.role)) redirect("/redacao?erro=" + encodeURIComponent("Esta área é da direção."));
  return s;
}
