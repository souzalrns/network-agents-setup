import { currentUser } from "@/lib/auth";
import { exportPublication } from "@/lib/backup";
import { humanCtx, isLead } from "@/lib/context";

/** Cópia de segurança da publicação em JSON (só a direção). Sem palavras-passe, sessões nem tokens. */
export async function GET() {
  const user = await currentUser();
  if (!user || !isLead(user.role)) return new Response("só a direção", { status: 403 });
  const data = await exportPublication(humanCtx(user.publicationId, user.userId, user.role, user.name));
  return new Response(JSON.stringify(data, null, 1), {
    headers: { "Content-Type": "application/json; charset=utf-8", "Content-Disposition": `attachment; filename="copia-${new Date().toISOString().slice(0, 10)}.json"`, "Cache-Control": "no-store" },
  });
}
