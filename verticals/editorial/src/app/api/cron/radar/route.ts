import { cronAuthorized } from "@/lib/cron";
import { runRadarAll } from "@/lib/radar";

/** Lê as fontes do radar cuja hora de consulta chegou, em todas as publicações. Chamar de 15 em 15 minutos. */
export async function POST(req: Request) {
  if (!cronAuthorized(req)) return Response.json({ error: "não autorizado" }, { status: 401 });
  const summaries = await runRadarAll();
  return Response.json({ summaries });
}
export const GET = POST;
