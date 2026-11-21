import { currentUser } from "@/lib/auth";
import { humanCtx, isLead } from "@/lib/context";
import { listSubscribers, subscribersCsv } from "@/lib/newsletter";

/** CSV das inscrições ativas (só a direção), com o link de anulação de cada pessoa. */
export async function GET(req: Request) {
  const user = await currentUser();
  if (!user || !isLead(user.role)) return new Response("só a direção", { status: 403 });
  const rows = await listSubscribers(humanCtx(user.publicationId, user.userId, user.role, user.name));
  const base = process.env.EDITORIAL_SITE_URL ?? new URL(req.url).origin;
  return new Response("﻿" + subscribersCsv(rows, base), {
    headers: { "Content-Type": "text/csv; charset=utf-8", "Content-Disposition": `attachment; filename="newsletter-${new Date().toISOString().slice(0, 10)}.csv"`, "Cache-Control": "no-store" },
  });
}
