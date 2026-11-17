import { NextResponse } from "next/server";
import { currentUser } from "@/lib/auth";
import { humanCtx } from "@/lib/context";
import { dbMessage } from "@/lib/db";
import { discardDraft, parseArticle, saveDraft } from "@/lib/drafts";
import { isUuid } from "@/lib/forms";
import { EditorialError } from "@/lib/stories";

/**
 * Autosave do artigo (D4). POST grava o rascunho no servidor; DELETE descarta-o.
 * Só aceita pedidos da própria origem (o cookie de sessão é SameSite=Lax, e a origem confirma-o).
 */
async function guard(req: Request, id: string) {
  const origin = req.headers.get("origin");
  const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host");
  if (origin && host && new URL(origin).host !== host) return { error: NextResponse.json({ error: "origem recusada" }, { status: 403 }) };
  if (!isUuid(id)) return { error: NextResponse.json({ error: "peça inválida" }, { status: 400 }) };
  const user = await currentUser();
  if (!user) return { error: NextResponse.json({ error: "sessão terminada: entra outra vez" }, { status: 401 }) };
  return { ctx: humanCtx(user.publicationId, user.userId, user.role, user.name) };
}

const fail = (e: unknown) => {
  const msg = e instanceof EditorialError ? e.message : dbMessage(e);
  if (!msg) console.error("[rascunho]", e);
  return NextResponse.json({ error: msg ?? "não foi possível guardar o rascunho" }, { status: msg ? 422 : 500 });
};

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const g = await guard(req, id);
  if (g.error) return g.error;
  let body: { rev?: unknown; baseVersion?: unknown; fields?: Record<string, unknown>; force?: unknown };
  try { body = await req.json(); } catch { return NextResponse.json({ error: "pedido inválido" }, { status: 400 }); }
  const baseVersion = Number(body.baseVersion);
  const rev = body.rev === null || body.rev === undefined ? null : Number(body.rev);
  if (!Number.isInteger(baseVersion) || (rev !== null && !Number.isInteger(rev)) || typeof body.fields !== "object" || !body.fields) {
    return NextResponse.json({ error: "pedido inválido" }, { status: 400 });
  }
  try {
    const fields = parseArticle((k) => body.fields![k]);
    const r = await saveDraft(g.ctx!, id, { rev, baseVersion, fields, force: body.force === true });
    return NextResponse.json(r, { status: r.status === "saved" ? 200 : 409, headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    return fail(e);
  }
}

export async function DELETE(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const g = await guard(req, id);
  if (g.error) return g.error;
  try {
    await discardDraft(g.ctx!, id);
    return NextResponse.json({ status: "discarded" });
  } catch (e) {
    return fail(e);
  }
}
