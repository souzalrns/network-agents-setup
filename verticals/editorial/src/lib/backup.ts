import type { Ctx } from "./context";
import { withCtx } from "./db";
import { EditorialError } from "./stories";

/**
 * Cópia de segurança da publicação, para a direcção descarregar: tudo o que a redacção produziu, em JSON.
 * Corre com o contexto da direcção, por isso o RLS limita-a a ESTA publicação. Ficam de fora, de propósito:
 * palavras-passe, sessões, tokens de API e de recuperação (segredos), e os bytes das imagens (a lista vai, o
 * conteúdo descarrega-se de /media/<id>).
 */
const TABLES = ["publications", "sections", "pages", "memberships", "stories", "story_versions", "story_events", "comments",
  "claims", "story_refs", "sources", "story_sources", "agent_outputs", "feed_sources", "feed_items", "distribution_items",
  "corrections", "story_drafts", "subscribers"] as const;

export async function exportPublication(ctx: Ctx): Promise<Record<string, unknown>> {
  if (ctx.kind !== "human" || !["admin", "director"].includes(ctx.role ?? "")) throw new EditorialError("A cópia de segurança é da direção.");
  return withCtx(ctx, async (tx) => {
    const out: Record<string, unknown> = { format: "editorial-backup/1", exported_at: new Date().toISOString(), publication_id: ctx.publicationId };
    for (const t of TABLES) {
      // stories tem uma coluna gerada de pesquisa (tsvector) que não interessa guardar
      out[t] = t === "stories"
        ? await tx.unsafe(`select to_jsonb(s) - 'search' as row from stories s order by created_at`).then((r) => r.map((x) => x.row))
        : await tx.unsafe(`select to_jsonb(x) as row from ${t} x`).then((r) => r.map((x) => x.row));
    }
    out.users = await tx`select id, name, email::text as email, created_at from users`;
    out.media = await tx`select id, filename, content_type, size, width, height, alt, credit, uploaded_by, created_at from media order by created_at`;
    return out;
  });
}
