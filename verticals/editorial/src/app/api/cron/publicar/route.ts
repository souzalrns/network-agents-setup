import { systemCtx } from "@/lib/context";
import { allPublications, cronAuthorized } from "@/lib/cron";
import { publishDue } from "@/lib/stories";

/** Publica as peças agendadas por uma pessoa cuja hora chegou. Chamar de 5 em 5 minutos. */
export async function POST(req: Request) {
  if (!cronAuthorized(req)) return Response.json({ error: "não autorizado" }, { status: 401 });
  const out: Record<string, string[]> = {};
  for (const id of await allPublications()) out[id] = await publishDue(systemCtx(id, "publicação agendada"));
  return Response.json({ published: out });
}
export const GET = POST;
