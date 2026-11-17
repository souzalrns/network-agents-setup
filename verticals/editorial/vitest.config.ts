import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const host = process.env.EDITORIAL_TEST_PG ?? "127.0.0.1:55432";
// cada frente de trabalho pode usar a sua base (EDITORIAL_TEST_DB) sem apagar a das outras
const dbName = process.env.EDITORIAL_TEST_DB ?? "editorial_test";

export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  test: {
    include: ["tests/**/*.test.ts"],
    globalSetup: ["tests/helpers/global-setup.ts"],
    fileParallelism: false,
    testTimeout: 20_000,
    hookTimeout: 60_000,
    env: {
      EDITORIAL_TEST_DB: dbName,
      EDITORIAL_TEST_OWNER_URL: `postgres://postgres:postgres@${host}/${dbName}`,
      EDITORIAL_DATABASE_URL: `postgres://editorial_app:app_local@${host}/${dbName}`,
    },
  },
});
