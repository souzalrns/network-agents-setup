import type { Ctx } from "./context";
import { type Tx, withCtx } from "./db";
import { EditorialError } from "./stories";

/**
 * Biblioteca de média na própria base (sem serviço de armazenamento externo). O browser reduz a imagem antes de
 * enviar (máx. 2000 px); o servidor confirma o tipo pelos primeiros bytes, não pelo nome nem pelo cabeçalho.
 */
export const MEDIA_MAX_BYTES = 3_000_000;
export const MEDIA_PATH = /^\/media\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

/** Tipo real pelos «números mágicos». Tudo o que não for JPEG, PNG ou WebP é recusado. */
export function sniffImage(b: Uint8Array): "image/jpeg" | "image/png" | "image/webp" | null {
  if (b.length > 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return "image/jpeg";
  if (b.length > 8 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return "image/png";
  if (b.length > 12 && String.fromCharCode(...b.slice(0, 4)) === "RIFF" && String.fromCharCode(...b.slice(8, 12)) === "WEBP") return "image/webp";
  return null;
}

export interface MediaRow { id: string; filename: string; content_type: string; size: number; width: number | null; height: number | null;
  alt: string; credit: string; created_at: Date; uploader: string | null }

export async function saveMedia(ctx: Ctx, input: { bytes: Uint8Array; filename: string; width?: number; height?: number; alt?: string; credit?: string }): Promise<string> {
  if (!input.bytes.length) throw new EditorialError("O ficheiro está vazio.");
  if (input.bytes.length > MEDIA_MAX_BYTES) throw new EditorialError("A imagem tem mais de 3 MB, mesmo depois de reduzida.");
  const type = sniffImage(input.bytes);
  if (!type) throw new EditorialError("Só se aceitam imagens JPEG, PNG ou WebP.");
  const dim = (n?: number) => (Number.isInteger(n) && n! > 0 && n! < 20_000 ? n! : null);
  return withCtx(ctx, async (tx) => {
    const [r] = await tx<{ id: string }[]>`insert into media (publication_id, filename, content_type, bytes, size, width, height, alt, credit, uploaded_by)
      values (${ctx.publicationId}, ${input.filename.slice(0, 200)}, ${type}, ${Buffer.from(input.bytes)}, ${input.bytes.length},
        ${dim(input.width)}, ${dim(input.height)}, ${(input.alt ?? "").slice(0, 300)}, ${(input.credit ?? "").slice(0, 200)}, ${ctx.userId ?? null})
      returning id`;
    return r!.id;
  });
}

export async function listMedia(tx: Tx, limit = 120): Promise<MediaRow[]> {
  return tx<MediaRow[]>`select m.id, m.filename, m.content_type, m.size, m.width, m.height, m.alt, m.credit, m.created_at,
      mb.display_name as uploader
    from media m left join memberships mb on mb.user_id = m.uploaded_by and mb.publication_id = m.publication_id
    order by m.created_at desc limit ${limit}`;
}

/** Os bytes de uma imagem, no contexto de quem pede (público pelo domínio, ou redacção). */
export async function readMedia(ctx: Ctx, id: string): Promise<{ bytes: Buffer; content_type: string } | null> {
  return withCtx(ctx, async (tx) => {
    const [r] = await tx<{ bytes: Buffer; content_type: string }[]>`select bytes, content_type from media where id = ${id}`;
    return r ?? null;
  });
}
