import { runAgent } from "./agents";
import { type Ctx, canWrite } from "./context";
import { withCtx } from "./db";

/**
 * Ponte entre a redacção e os agentes: uma pessoa com papel de escrita pede, o agente corre com a sua
 * própria identidade (`agent`, sem acesso a fontes nem a comentários) e deixa uma proposta para rever.
 */
const IDS = { research: "editorial.research", factcheck: "editorial.factcheck", editor: "editorial.editor" } as const;

export async function runAgentForStory(ctx: Ctx, agent: keyof typeof IDS, storyId: string): Promise<{ ok: boolean; message: string }> {
  if (ctx.kind !== "human" || !canWrite(ctx.role)) return { ok: false, message: "O teu papel não pede trabalho aos agentes." };
  // a pessoa tem de conseguir ver a peça (mesma publicação); o agente não herda mais nada dela
  const [visible] = await withCtx(ctx, (tx) => tx`select 1 from stories where id = ${storyId}`);
  if (!visible) return { ok: false, message: "Não encontrei a peça." };
  const r = await runAgent(ctx.publicationId, IDS[agent], { storyId });
  await withCtx(ctx, (tx) => tx`insert into audit_log (publication_id, actor_kind, actor_user_id, actor_label, action, entity, entity_id, payload)
    values (${ctx.publicationId}, 'human', ${ctx.userId!}, ${ctx.label ?? ""}, 'agent.request', 'story', ${storyId},
      ${tx.json({ agent_id: IDS[agent], run_id: r.runId, status: r.status })})`);
  if (r.status === "failed") return { ok: false, message: `${r.displayName} não concluiu: ${r.reason}` };
  const extra = r.status === "stopped" ? ` (parou no limite de custo: ${r.reason}; ficou a parte sem modelo)` : "";
  return { ok: true, message: `${r.displayName} deixou uma proposta para rever${extra}.` };
}

export async function runRadarSuggestions(ctx: Ctx): Promise<{ ok: boolean; message: string }> {
  if (ctx.kind !== "human" || !canWrite(ctx.role)) return { ok: false, message: "O teu papel não pede trabalho aos agentes." };
  const r = await runAgent(ctx.publicationId, "editorial.radar");
  if (r.status === "failed") return { ok: false, message: `${r.displayName} não concluiu: ${r.reason}` };
  return { ok: true, message: `${r.displayName} deixou sugestões de pautas para rever.` };
}
