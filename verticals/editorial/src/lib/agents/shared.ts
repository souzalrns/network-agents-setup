/** Peças comuns aos agentes: opções de execução, envelope da saída e leitura da peça. */
import { randomUUID } from "node:crypto";
import type { Ctx } from "../context";
import type { Tx } from "../db";
import { getStory, type Story } from "../stories";
import { type AgentId, type LlmInfo, OUTPUT_KIND, type OutputBase } from "./contracts";
import { Budget, type LlmClient, type LlmEnv, limitsFromEnv, llmFromEnv, type RunLimits } from "./llm";

export interface AgentOpts {
  runId?: string;
  /** `undefined`: usa o ambiente (GEMINI_API_KEY); `null`: sem modelo. */
  llm?: LlmClient | null;
  limits?: Partial<RunLimits>;
  now?: Date;
}

export interface AgentEnv extends LlmEnv { runId: string; now: Date }

export function agentEnv(opts: AgentOpts = {}): AgentEnv {
  return {
    runId: opts.runId ?? newRunId(),
    llm: opts.llm === undefined ? llmFromEnv() : opts.llm,
    budget: new Budget({ ...limitsFromEnv(), ...opts.limits }),
    now: opts.now ?? new Date(),
  };
}

export const newRunId = () => `run_${randomUUID()}`;

/** O que uma função de agente devolve ao executor: a saída e, opcionalmente, uma nota para a peça. */
export interface AgentResult<T> { output: T; note?: string; llm: LlmInfo }

export const LLM_SKIPPED: LlmInfo = { status: "skipped", model: "", reason: "" };

export function envelope<K extends OutputBase["kind"]>(agentId: AgentId, env: AgentEnv, inputs: Record<string, unknown>,
  sourcesUsed: string[], llm: LlmInfo, notes: string[] = []): OutputBase & { kind: K } {
  return {
    schema_version: 1,
    agent_id: agentId,
    run_id: env.runId,
    kind: OUTPUT_KIND[agentId] as K,
    generated_at: env.now.toISOString(),
    proposal: true,
    inputs,
    sources_used: [...new Set(sourcesUsed.filter((u) => /^https?:\/\//i.test(u)))],
    cost: { ...env.budget.cost },
    llm,
    notes,
  };
}

export class AgentError extends Error {}

/** A peça, tal como o agente a pode ler (RLS: só da sua publicação). */
export async function storyFor(tx: Tx, ctx: Ctx, storyId: string): Promise<Story> {
  if (ctx.kind !== "agent") throw new AgentError("os agentes correm sempre com contexto de agente");
  const s = await getStory(tx, storyId);
  if (!s) throw new AgentError("não encontrei a peça nesta publicação");
  return s;
}

export interface RefRow { id: string; kind: string; url: string; title: string; credit: string; note: string; added_kind: string }
export const loadRefs = (tx: Tx, storyId: string) =>
  tx<RefRow[]>`select id, kind, url, title, credit, note, added_kind from story_refs where story_id = ${storyId} order by created_at`;

export interface ClaimRow {
  id: string; text: string; kind: string; attributed_to: string; evidence: unknown; verification: string; in_article: boolean; origin: string;
}
export const loadClaims = (tx: Tx, storyId: string) =>
  tx<ClaimRow[]>`select id, text, kind, attributed_to, evidence, verification, in_article, origin
                 from claims where story_id = ${storyId} order by created_at`;
