// Local config so vitest does not pick up the monorepo's root vitest.config.ts (include: tests/**)
// when this terminal lives inside network-agents-setup.
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["src/**/*.test.ts"],
  },
});
