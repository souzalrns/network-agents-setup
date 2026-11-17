/**
 * Executor dos agentes: corre UM agente para uma peça (ou para a publicação, no caso do radar), com um
 * identificador de execução, regista início, fim e falha no `audit_log` (actor_kind agent), valida e guarda
 * a proposta em `agent_outputs` (estado `proposed`) e devolve-a. Quem aceita ou rejeita é sempre uma pessoa.
 */
import { agentCtx, type Ctx } from "../context";
import { type Tx, withCtx } from "../db";
import { agentName, type Publication } from "../publication";
import { type AgentId, type AgentOutput, isAgentId, type LlmInfo, validateOutput } from "./contracts";
import { reviewArticle } from "./editor";
import { checkStory } from "./factcheck";
import { suggestFromRadar, type RadarOpts } from "./radar-suggest";
import { buildDossier } from "./research";
import { type AgentResult, newRunId } from "./shared";

/** Nome de apresentação: o configurado na publicação (`agent_names`) ou um nome neutro. */
export function agentDisplayName(publication: Pick<Publication, "agent_names"> | null | undefined, id: string): string {
  return agentName({ agent_names: publication?.agent_names ?? {} }, id);
}

export interface RunTarget { storyId?: string }
export type RunOptions = RadarOpts;

export interface RunResult {
  runId: string;
  agentId: string;
  displayName: string;
  /** completed: tudo correu; stopped: o passo com modelo parou por limite (a parte determinística foi guardada); failed: nada guardado. */
  status: "completed" | "stopped" | "failed";
  outputId: string | null;
  output: AgentOutput | null;
  reason: string;
}

async function audit(ctx: Ctx, action: string, entityId: string, payload: Record<string, unknown>, tx?: Tx) {
  const write = (t: Tx) => t`insert into audit_log (publication_id, actor_kind, actor_label, action, entity, entity_id, payload)
    values (${ctx.publicationId}, 'agent', ${ctx.label ?? ""}, ${action}, 'agent_run', ${entityId}, ${t.json(payload as never)})`;
  if (tx) await write(tx);
  else await withCtx(ctx, write);
}

async function execute(ctx: Ctx, agentId: AgentId, target: RunTarget, opts: RunOptions): Promise<AgentResult<AgentOutput>> {
  if (agentId === "editorial.radar") return suggestFromRadar(ctx, ctx.publicationId, opts);
  if (!target.storyId) throw new Error("este agente precisa de uma peça");
  switch (agentId) {
    case "editorial.editor": return reviewArticle(ctx, target.storyId, opts);
    case "editorial.factcheck": return checkStory(ctx, target.storyId, opts);
    case "editorial.research": return buildDossier(ctx, target.storyId, opts);
  }
}

export async function runAgent(publicationId: string, agentId: string, target: RunTarget = {}, opts: RunOptions = {}): Promise<RunResult> {
  const runId = opts.runId ?? newRunId();
  if (!isAgentId(agentId)) {
    return { runId, agentId, displayName: agentId, status: "failed", outputId: null, output: null, reason: "agente desconhecido" };
  }
  const ctx = agentCtx(publicationId, agentId);
  const [pub] = await withCtx(ctx, (tx) => tx<Pick<Publication, "agent_names">[]>`select agent_names from publications where id = ${publicationId}`);
  const displayName = agentDisplayName(pub, agentId);
  const base = { runId, agentId, displayName };
  if (!pub) return { ...base, status: "failed", outputId: null, output: null, reason: "publicação inexistente" };

  const storyId = agentId === "editorial.radar" ? null : target.storyId ?? null;
  await audit(ctx, "agent.run.start", runId, { run_id: runId, agent_id: agentId, display_name: displayName, story_id: storyId });

  try {
    const result = await execute(ctx, agentId, target, { ...opts, runId });
    const valid = validateOutput(result.output);
    if (!valid.ok) throw new Error(`saída do agente fora do contrato: ${valid.errors.slice(0, 5).join("; ")}`);
    const output = valid.value;
    const llm: LlmInfo = result.llm;
    const status: RunResult["status"] = llm.status === "stopped" ? "stopped" : "completed";

    const outputId = await withCtx(ctx, async (tx) => {
      const [row] = await tx<{ id: string }[]>`
        insert into agent_outputs (publication_id, story_id, agent_id, kind, run_id, payload, cost, status)
        values (${publicationId}, ${storyId}, ${agentId}, ${output.kind}, ${runId}, ${tx.json(output as never)},
                ${tx.json(output.cost as never)}, 'proposed')
        returning id`;
      const id = row!.id;
      if (storyId) {
        await tx`insert into story_events (publication_id, story_id, type, actor_kind, actor_label, payload)
                 values (${publicationId}, ${storyId}, 'agent_output', 'agent', ${agentId},
                         ${tx.json({ output_id: id, kind: output.kind, run_id: runId })})`;
        if (result.note) {
          // sem RETURNING: um agente escreve notas mas não lê comentários
          await tx`insert into comments (publication_id, story_id, author_kind, author_label, body, kind)
                   values (${publicationId}, ${storyId}, 'agent', ${displayName}, ${`${result.note} [proposta ${id}]`}, 'agent_note')`;
        }
      }
      if (llm.status === "rejected") {
        await audit(ctx, "agent.llm.rejected", runId, { run_id: runId, agent_id: agentId, model: llm.model, reason: llm.reason }, tx);
      }
      await audit(ctx, status === "stopped" ? "agent.run.stopped" : "agent.run.finish", runId, {
        run_id: runId, agent_id: agentId, output_id: id, kind: output.kind, story_id: storyId, cost: output.cost,
        llm_status: llm.status, reason: llm.reason,
      }, tx);
      return id;
    });
    return { ...base, status, outputId, output, reason: status === "stopped" ? llm.reason : "" };
  } catch (e) {
    const reason = (e as Error).message?.slice(0, 900) || "erro desconhecido";
    await audit(ctx, "agent.run.failed", runId, { run_id: runId, agent_id: agentId, story_id: storyId, error: reason });
    return { ...base, status: "failed", outputId: null, output: null, reason };
  }
}
