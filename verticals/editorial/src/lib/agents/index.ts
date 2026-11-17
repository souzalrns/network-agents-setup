/** Agentes da redacção: propõem, nunca decidem. */
export * from "./contracts";
export { reviewArticle, reviewText, adaptations } from "./editor";
export { checkStory, classify, extractCheckable, contradictions } from "./factcheck";
export { buildDossier, suggestPrimarySources, PRIMARY_SOURCES } from "./research";
export { suggestFromRadar, clusterItems, scoreCluster, type RadarOpts, type RadarItem } from "./radar-suggest";
export { runAgent, agentDisplayName, type RunResult, type RunTarget, type RunOptions } from "./run";
export {
  type LlmClient, type LlmRequest, type LlmResponse, type RunLimits, Budget, BudgetExceeded, GeminiClient, llmFromEnv, limitsFromEnv,
  estimateUsd,
} from "./llm";
export { type AgentOpts, type AgentResult, AgentError, newRunId } from "./shared";
