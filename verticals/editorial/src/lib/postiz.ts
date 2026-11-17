import { createHash } from "node:crypto";
import type { Ctx } from "./context";
import { withCtx } from "./db";

/**
 * Envio de conteúdos de distribuição APROVADOS para o Postiz (agendador open source, AGPL-3.0, serviço à
 * parte). Mesmo contrato do `runner/plan_runner/postiz.py` (docs/ops/POSTIZ.md):
 * - só rascunhos (`type: draft`): a pessoa revê e agenda no Postiz; publicar no momento não existe aqui;
 * - só itens com aprovação humana registada (approved_by), de peças aprovadas, agendadas ou publicadas;
 * - idempotente: cada item leva o sha256 do que se envia e não se reenvia;
 * - POSTIZ_API_URL e POSTIZ_API_KEY só do ambiente; sem eles, simula e diz o que enviaria.
 */
const NETWORKS: Record<string, string[]> = { instagram: ["instagram", "instagram-standalone"], youtube: ["youtube"] };

export interface DispatchItem {
  id: string; channel: string; status: "enviado" | "simulado" | "ja_enviado" | "recusado" | "erro"; reason?: string; ref?: string;
}

export interface PostizTransport {
  integrations(): Promise<{ id: string; identifier: string; disabled?: boolean }[]>;
  createPost(payload: unknown): Promise<{ id?: string } | unknown>;
}

export function httpTransport(url = process.env.POSTIZ_API_URL, key = process.env.POSTIZ_API_KEY): PostizTransport | null {
  if (!url || !key) return null;
  const base = url.replace(/\/+$/, "");
  const call = async (method: string, path: string, body?: unknown) => {
    const r = await fetch(base + path, {
      method, headers: { Authorization: key, "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(20_000),
    });
    if (!r.ok) throw new Error(`Postiz respondeu ${r.status}`);
    return r.json();
  };
  return {
    integrations: () => call("GET", "/integrations") as Promise<{ id: string; identifier: string; disabled?: boolean }[]>,
    createPost: (payload) => call("POST", "/posts", payload),
  };
}

const escapeHtml = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const toHtml = (text: string) => text.split("\n").filter((l) => l.trim()).map((l) => `<p>${escapeHtml(l)}</p>`).join("");

export function buildPayload(item: { channel: string; content: Record<string, unknown> }, integrationId: string, siteUrl: string) {
  const text = String(item.content.text ?? "").trim();
  const link = String(item.content.link ?? "");
  const full = link ? `${text}\n${link.startsWith("http") ? link : siteUrl.replace(/\/+$/, "") + link}` : text;
  const settings: Record<string, unknown> = item.channel === "instagram" ? { __type: "instagram", post_type: "post" }
    : { __type: item.channel, title: String(item.content.title ?? text.split("\n")[0]).slice(0, 100), type: "public" };
  return {
    type: "draft", date: new Date(Date.now() + 3_600_000).toISOString(), shortLink: false, tags: [],
    posts: [{ integration: { id: integrationId }, value: [{ content: toHtml(full), image: [] }], settings }],
  };
}

export async function dispatchApproved(ctx: Ctx, opts: { transport?: PostizTransport | null; siteUrl?: string } = {}): Promise<DispatchItem[]> {
  if (ctx.kind !== "human" || !["admin", "director", "editor"].includes(ctx.role ?? "")) {
    throw new Error("Só a edição ou a direção envia para o agendador.");
  }
  const transport = opts.transport === undefined ? httpTransport() : opts.transport;
  const siteUrl = opts.siteUrl ?? process.env.EDITORIAL_SITE_URL ?? "";
  return withCtx(ctx, async (tx) => {
    const items = await tx<{ id: string; channel: string; content: Record<string, unknown>; external_ref: string; approved_by: string | null; story_state: string }[]>`
      select d.id, d.channel, d.content, d.external_ref, d.approved_by, s.state as story_state
      from distribution_items d join stories s on s.id = d.story_id
      where d.state = 'approved' and d.approved_hash = editorial.distribution_hash(d.channel, d.content) order by d.created_at`;
    const integrations = transport ? await transport.integrations() : [];
    const out: DispatchItem[] = [];
    for (const it of items) {
      const sha = createHash("sha256").update(JSON.stringify([it.channel, it.content])).digest("hex");
      if (it.external_ref.startsWith(`sha256:${sha}`)) { out.push({ id: it.id, channel: it.channel, status: "ja_enviado" }); continue; }
      if (!it.approved_by || !["approved", "scheduled", "published"].includes(it.story_state)) {
        out.push({ id: it.id, channel: it.channel, status: "recusado", reason: "sem aprovação humana" }); continue;
      }
      const text = String(it.content.text ?? "");
      if (!text.trim() || text.includes("[[A DEFINIR]]")) { out.push({ id: it.id, channel: it.channel, status: "recusado", reason: "texto vazio ou por definir" }); continue; }
      const ids = NETWORKS[it.channel];
      if (!ids) { out.push({ id: it.id, channel: it.channel, status: "recusado", reason: "canal sem integração no Postiz (preparar à mão)" }); continue; }
      if (!transport) { out.push({ id: it.id, channel: it.channel, status: "simulado", reason: "POSTIZ_API_URL/POSTIZ_API_KEY por configurar" }); continue; }
      const match = integrations.filter((i) => ids.includes(i.identifier) && !i.disabled);
      if (match.length !== 1) { out.push({ id: it.id, channel: it.channel, status: "recusado", reason: `${match.length} integrações ${it.channel} activas no Postiz (é preciso 1)` }); continue; }
      try {
        const res = await transport.createPost(buildPayload(it, match[0]!.id, siteUrl)) as { id?: string } | { id?: string }[];
        const ref = Array.isArray(res) ? res[0]?.id : res?.id;
        // ponto de gravação: se a base de dados recusar este item, os outros (já aceites pelo Postiz) ficam registados
        try {
          await tx.savepoint((sp) => sp`update distribution_items set state = 'handed_off', external_ref = ${`sha256:${sha} postiz:${ref ?? "?"}`} where id = ${it.id}`);
          out.push({ id: it.id, channel: it.channel, status: "enviado", ref: ref ?? undefined });
        } catch (e) {
          out.push({ id: it.id, channel: it.channel, status: "erro", ref: ref ?? undefined, reason: `enviado ao Postiz mas não registado: ${(e as Error).message}` });
        }
      } catch (e) {
        out.push({ id: it.id, channel: it.channel, status: "erro", reason: (e as Error).message });
      }
    }
    await tx`insert into audit_log (publication_id, actor_kind, actor_user_id, actor_label, action, entity, payload)
      values (${ctx.publicationId}, 'human', ${ctx.userId!}, ${ctx.label ?? ""}, 'distribution.dispatch', 'postiz', ${tx.json(out as never)})`;
    return out;
  });
}
