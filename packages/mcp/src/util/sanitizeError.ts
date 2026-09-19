/**
 * Evita expor detalhe tecnico ao cliente (stack traces, paths de ficheiro,
 * IPs internos, nomes de tabela) em erros devolvidos pelas tools MCP.
 * O detalhe completo fica no log interno (console.error); o cliente só
 * recebe uma mensagem generica que nomeia a operacao, nao a causa.
 *
 * `context` e a frase que segue "Erro " (ex. "ao ler ficheiro" ->
 * "Erro ao ler ficheiro").
 */
export function toClientError(error: unknown, context: string): string {
  // eslint-disable-next-line no-console
  console.error(`Erro ${context}:`, error);
  return `Erro ${context}`;
}
