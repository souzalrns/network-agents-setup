import { NextResponse } from "next/server";
import { currentUser } from "@/lib/auth";
import { humanCtx } from "@/lib/context";
import { dbMessage } from "@/lib/db";
import { MEDIA_MAX_BYTES, saveMedia } from "@/lib/media";
import { EditorialError } from "@/lib/stories";

/** Carregar uma imagem para a biblioteca (multipart). Mesma origem, sessão obrigatória; o tipo confirma-se pelos bytes. */
export async function POST(req: Request) {
  const origin = req.headers.get("origin");
  const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host");
  if (origin && host && new URL(origin).host !== host) return NextResponse.json({ error: "origem recusada" }, { status: 403 });
  const user = await currentUser();
  if (!user) return NextResponse.json({ error: "sessão terminada: entra outra vez" }, { status: 401 });
  if (Number(req.headers.get("content-length") ?? 0) > MEDIA_MAX_BYTES + 100_000) return NextResponse.json({ error: "a imagem tem mais de 3 MB" }, { status: 413 });
  let form: FormData;
  try { form = await req.formData(); } catch { return NextResponse.json({ error: "pedido inválido" }, { status: 400 }); }
  const file = form.get("file");
  if (!(file instanceof File)) return NextResponse.json({ error: "falta o ficheiro" }, { status: 400 });
  try {
    const id = await saveMedia(humanCtx(user.publicationId, user.userId, user.role, user.name), {
      bytes: new Uint8Array(await file.arrayBuffer()), filename: file.name,
      width: Number(form.get("width")) || undefined, height: Number(form.get("height")) || undefined,
      alt: String(form.get("alt") ?? ""), credit: String(form.get("credit") ?? ""),
    });
    return NextResponse.json({ id, url: `/media/${id}` });
  } catch (e) {
    const msg = e instanceof EditorialError ? e.message : dbMessage(e);
    if (!msg) console.error("[média]", e);
    return NextResponse.json({ error: msg ?? "não foi possível guardar a imagem" }, { status: msg ? 422 : 500 });
  }
}
