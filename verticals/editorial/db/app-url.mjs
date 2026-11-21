// Ligação da aplicação (papel editorial_app) quando só existe a ligação do dono (ex.: integração Neon do Vercel,
// que cria DATABASE_URL e DATABASE_URL_UNPOOLED). A palavra-passe do editorial_app é DERIVADA da do dono
// (sha256), por isso não há segredo novo para guardar: o passo de preparação e a aplicação calculam a mesma.
// Partilhado por db/provision.mjs e src/lib/db.ts.
import { createHash } from "node:crypto";

export const APP_ROLE = "editorial_app";

/** Palavra-passe do editorial_app derivada da ligação do dono. */
export function derivedAppPassword(ownerUrl) {
  const u = new URL(ownerUrl);
  return createHash("sha256").update(`editorial_app:${decodeURIComponent(u.password)}:${u.hostname}`).digest("base64url");
}

/** A mesma base e o mesmo servidor (pooled, se houver), mas com o papel editorial_app. */
export function appUrlFrom(pooledUrl, ownerUrl) {
  const u = new URL(pooledUrl);
  u.username = APP_ROLE;
  u.password = derivedAppPassword(ownerUrl);
  return u.toString();
}

/** Ligação do dono, para migrações, sementeira e para derivar a palavra-passe do editorial_app. */
export function ownerDatabaseUrl(env = process.env) {
  return env.EDITORIAL_MIGRATION_URL ?? env.DATABASE_URL_UNPOOLED ?? env.POSTGRES_URL_NON_POOLING;
}

/**
 * Ligação da aplicação a partir do ambiente:
 * 1. EDITORIAL_DATABASE_URL, se existir (configuração explícita, como no README);
 * 2. senão, derivada da MESMA ligação do dono que o build usa (ownerDatabaseUrl: assim o build e a aplicação
 *    calculam sempre a mesma palavra-passe), no servidor pooled (DATABASE_URL ou POSTGRES_URL).
 */
export function appDatabaseUrl(env = process.env) {
  if (env.EDITORIAL_DATABASE_URL) return env.EDITORIAL_DATABASE_URL;
  const owner = ownerDatabaseUrl(env) ?? env.DATABASE_URL ?? env.POSTGRES_URL;
  const pooled = env.DATABASE_URL ?? env.POSTGRES_URL ?? owner;
  return owner && pooled ? appUrlFrom(pooled, owner) : undefined;
}
