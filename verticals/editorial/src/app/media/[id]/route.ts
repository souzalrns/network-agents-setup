import { headers } from "next/headers";
import { currentUser } from "@/lib/auth";
import { humanCtx } from "@/lib/context";
import { readMedia } from "@/lib/media";
import { publicContext } from "@/lib/publication";

/**
 * Serve uma imagem da biblioteca. A publicação vem do domínio (ou da sessão da redação); a imagem nunca muda
 * (não se substitui, só se apaga), por isso pode ficar em cache para sempre.
 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) return new Response("não encontrado", { status: 404 });
  const user = await currentUser();
  const h = await headers();
  const ctx = user ? humanCtx(user.publicationId, user.userId, user.role, user.name) : await publicContext(h.get("x-forwarded-host") ?? h.get("host"));
  const m = ctx ? await readMedia(ctx, id) : null;
  if (!m) return new Response("não encontrado", { status: 404 });
  return new Response(new Uint8Array(m.bytes), {
    headers: {
      "Content-Type": m.content_type,
      "Cache-Control": user ? "private, max-age=3600" : "public, max-age=31536000, immutable",
      "X-Content-Type-Options": "nosniff",
      "Content-Security-Policy": "default-src 'none'; sandbox",
    },
  });
}
