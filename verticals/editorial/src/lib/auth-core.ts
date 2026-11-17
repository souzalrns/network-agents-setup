import { type Ctx, humanCtx, type Role } from "./context";
import { db } from "./db";
import { newToken, tokenHash, verifyPassword } from "./password";

export interface SessionUser {
  userId: string;
  name: string;
  email: string;
  publicationId: string;
  role: Role;
}

export const SESSION_DAYS = 14;
// hash de uma palavra-passe que ninguém tem: iguala o tempo de resposta quando o email não existe
const DUMMY = "scrypt$32768$8$1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

export type LoginResult =
  | { ok: true; token: string; expires: Date; user: { id: string; name: string }; publicationId: string }
  | { ok: false; reason: "credentials" | "no_access" };

/** Entrada com email e palavra-passe. `publicationSlug` escolhe a publicação quando a pessoa pertence a várias. */
export async function login(email: string, password: string, publicationSlug?: string): Promise<LoginResult> {
  const sql = db();
  const [user] = await sql<{ id: string; name: string; password_hash: string }[]>`
    select * from editorial.auth_user_by_email(${email.trim().toLowerCase()})`;
  const ok = await verifyPassword(password, user?.password_hash ?? DUMMY);
  if (!user || !ok) return { ok: false, reason: "credentials" };
  const pubs = await sql<{ publication_id: string; slug: string }[]>`select * from editorial.auth_memberships(${user.id})`;
  const pub = publicationSlug ? pubs.find((p) => p.slug === publicationSlug) : pubs[0];
  if (!pub) return { ok: false, reason: "no_access" };
  const token = newToken();
  const expires = new Date(Date.now() + SESSION_DAYS * 86_400_000);
  await sql`select editorial.auth_session_create(${tokenHash(token)}, ${user.id}, ${pub.publication_id}, ${expires})`;
  return { ok: true, token, expires, user: { id: user.id, name: user.name }, publicationId: pub.publication_id };
}

export async function sessionFromToken(token: string | undefined): Promise<SessionUser | null> {
  if (!token) return null;
  const [row] = await db()<{ user_id: string; name: string; email: string; publication_id: string; role: Role }[]>`
    select * from editorial.auth_session_get(${tokenHash(token)})`;
  if (!row) return null;
  return { userId: row.user_id, name: row.name, email: row.email, publicationId: row.publication_id, role: row.role };
}

export async function logout(token: string | undefined): Promise<void> {
  if (token) await db()`select editorial.auth_session_delete(${tokenHash(token)})`;
}

export const ctxOf = (s: SessionUser): Ctx => humanCtx(s.publicationId, s.userId, s.role, s.name);

export interface AgentToken { tokenId: string; publicationId: string; name: string; scopes: string[] }

/** Resolve um token de agente (cabeçalho Authorization: Bearer). Tokens revogados não resolvem. */
export async function agentFromToken(token: string | undefined): Promise<AgentToken | null> {
  if (!token) return null;
  const [row] = await db()<{ token_id: string; publication_id: string; name: string; scopes: string[] }[]>`
    select * from editorial.auth_api_token(${tokenHash(token)})`;
  return row ? { tokenId: row.token_id, publicationId: row.publication_id, name: row.name, scopes: row.scopes } : null;
}
