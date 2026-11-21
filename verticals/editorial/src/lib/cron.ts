import { timingSafeEqual } from "node:crypto";
import { systemCtx } from "./context";
import { db } from "./db";
import { publishDue } from "./stories";

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

/**
 * Publicação agendada sem depender de tarefas frequentes (no plano Hobby do Vercel correm uma vez por dia):
 * cada visita publica as peças cuja hora chegou, no máximo uma vez por minuto em cada instância. Corre como
 * «sistema», que só pode publicar o que uma pessoa agendou, sem tocar no conteúdo e com as afirmações
 * verificadas (regras da base de dados). Nunca falha a página: um erro aqui fica só no registo.
 */
const lastRun = new Map<string, number>();
export async function publishDueOpportunistic(publicationId: string, minIntervalMs = 60_000): Promise<string[]> {
  const now = Date.now();
  if (now - (lastRun.get(publicationId) ?? 0) < minIntervalMs) return [];
  lastRun.set(publicationId, now);
  try {
    return await publishDue(systemCtx(publicationId, "publicação agendada"));
  } catch (e) {
    console.error("[publicação agendada]", (e as Error).message);
    return [];
  }
}
