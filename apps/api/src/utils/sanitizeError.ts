import { getGlobalLogger } from '@network-agents/observability';

/**
 * Evita expor detalhe tecnico ao cliente (stack traces, paths, IPs internos,
 * mensagens de driver de BD) em respostas HTTP/WebSocket. O detalhe completo
 * fica no logger interno; o cliente só recebe uma mensagem generica que
 * nomeia a operacao, nao a causa.
 *
 * `context` e a frase que segue "Erro " (ex. "ao aprovar pedido" ->
 * "Erro ao aprovar pedido"). Mesma assinatura que
 * packages/mcp/src/util/sanitizeError.ts, por consistencia entre os 2 pacotes.
 */
export function toClientError(error: unknown, context: string): string {
  const logger = getGlobalLogger();
  logger.error(`Erro ${context}`, {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
  });
  return `Erro ${context}`;
}
