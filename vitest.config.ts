import { defineConfig } from 'vitest/config';
import { resolve } from 'path';

/**
 * Sem estes aliases, os testes não resolvem os pacotes do workspace
 * (@network-agents/*), porque nenhum pacote tem build publicado em dist/.
 * Apontamos diretamente para o src de cada um.
 */
const pkg = (name: string) => resolve(__dirname, `packages/${name}/src/index.ts`);

export default defineConfig({
  resolve: {
    alias: {
      '@network-agents/shared': pkg('shared'),
      '@network-agents/observability': pkg('observability'),
      '@network-agents/memory': pkg('memory'),
      '@network-agents/mcp': pkg('mcp'),
      '@network-agents/core': pkg('core'),
      '@network-agents/langgraph': pkg('langgraph'),
    },
  },
  test: {
    include: ['tests/**/*.test.ts'],
    testTimeout: 20000,
    reporters: ['default'],
  },
});
