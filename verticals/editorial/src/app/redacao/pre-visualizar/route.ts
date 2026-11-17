import { NextResponse } from "next/server";
import { currentUser } from "@/lib/auth";
import { renderMarkdown } from "@/lib/markdown";

/** Pré-visualização ao vivo do texto: o mesmo renderMarkdown do site, no servidor (nada de HTML montado no browser). */
export async function POST(req: Request) {
  if (!(await currentUser())) return NextResponse.json({ error: "sessão terminada" }, { status: 401 });
  let md = "";
  try { md = String((await req.json()).body ?? "").slice(0, 200_000); } catch { return NextResponse.json({ error: "pedido inválido" }, { status: 400 }); }
  return NextResponse.json({ html: renderMarkdown(md) }, { headers: { "Cache-Control": "no-store" } });
}
