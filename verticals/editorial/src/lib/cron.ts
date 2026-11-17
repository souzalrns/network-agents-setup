import { timingSafeEqual } from "node:crypto";
import { db } from "./db";

/** As tarefas automáticas só correm com o segredo CRON_SECRET (cabeçalho Authorization: Bearer). */
export function cronAuthorized(req: Request): boolean {
  const secret = process.env.CRON_SECRET;
  if (!secret || secret.length < 24) return false;
  const got = (req.headers.get("authorization") ?? "").replace(/^Bearer\s+/i, "");
  const a = Buffer.from(got), b = Buffer.from(secret);
  return a.length === b.length && timingSafeEqual(a, b);
}

export async function allPublications(): Promise<string[]> {
  return (await db()<{ id: string }[]>`select id from editorial.system_publications()`).map((r) => r.id);
}
