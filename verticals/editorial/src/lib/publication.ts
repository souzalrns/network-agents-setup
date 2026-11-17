import { type Ctx, publicCtx } from "./context";
import { db, withCtx } from "./db";

export interface Publication {
  id: string; slug: string; name: string; tagline: string; description: string;
  logo_url: string | null; favicon_url: string | null; primary_color: string; secondary_color: string;
  domain: string | null; language: string; timezone: string; contact_email: string | null; contact_address: string | null;
  social_links: Record<string, string>; legal: Record<string, string>; agent_names: Record<string, string>;
  settings: Record<string, unknown>; public_launch: boolean;
}

export async function getPublication(ctx: Ctx): Promise<Publication> {
  const [p] = await withCtx(ctx, (tx) => tx<Publication[]>`select * from publications where id = ${ctx.publicationId}`);
  if (!p) throw new Error("Publicação não encontrada.");
  return p;
}

/**
 * A publicação servida pelo site público: a do domínio do pedido ou, sem domínio próprio, a de
 * EDITORIAL_DEFAULT_PUBLICATION. Devolve o contexto público (só lê o que está publicado).
 */
export async function publicContext(host: string | null): Promise<Ctx | null> {
  const fallback = process.env.EDITORIAL_DEFAULT_PUBLICATION ?? "";
  const clean = (host ?? "").split(":")[0]!.toLowerCase();
  const [row] = await db()<{ id: string | null }[]>`select editorial.public_publication(${clean}, ${fallback}) as id`;
  return row?.id ? publicCtx(row.id) : null;
}

/** Nome de apresentação de um agente: o da configuração da publicação, ou um nome neutro. */
export const AGENT_FALLBACK_NAMES: Record<string, string> = {
  "editorial.radar": "Radar",
  "editorial.research": "Investigação",
  "editorial.factcheck": "Verificação",
  "editorial.editor": "Edição assistida",
};
export function agentName(p: Pick<Publication, "agent_names">, id: string): string {
  return p.agent_names?.[id] || AGENT_FALLBACK_NAMES[id] || id;
}
