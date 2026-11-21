import type { Ctx } from "./context";
import { db, withCtx } from "./db";
import { hashPassword, newToken, tokenHash } from "./password";

/**
 * Recuperar a palavra-passe sem serviço de email: a direcção gera um link de uso único (24 h) e entrega-o à
 * pessoa por um canal seguro. Só o hash do token fica na base; o token existe apenas no link.
 */
export async function createResetLink(ctx: Ctx, userId: string, baseUrl: string): Promise<{ link: string; expires: Date }> {
  const token = newToken();
  const expires = await withCtx(ctx, async (tx) => {
    const [r] = await tx<{ e: Date }[]>`select editorial.staff_reset_link(${userId}, ${tokenHash(token)}) as e`;
    return r!.e;
  });
  return { link: `${baseUrl.replace(/\/+$/, "")}/redacao/recuperar/${token}`, expires };
}

/** Troca a palavra-passe com um token válido. Devolve false se o link expirou, já foi usado ou não existe. */
export async function resetPassword(token: string, password: string): Promise<boolean> {
  if (!/^[A-Za-z0-9_-]{20,100}$/.test(token)) return false;
  const hash = await hashPassword(password);
  const [r] = await db()<{ ok: boolean }[]>`select editorial.auth_reset_password(${tokenHash(token)}, ${hash}) as ok`;
  return r?.ok === true;
}
