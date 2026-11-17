// Testes no browser numa base PRÓPRIA e descartável: nunca tocam na base de desenvolvimento.
// 1. apaga e recria E2E_DB (omissão editorial_e2e), aplica as migrações e semeia o exemplo neutro;
// 2. arranca a aplicação (next start) apontada a essa base, na porta E2E_PORT (omissão 3100);
// 3. corre o fluxo completo (run.mjs) e as medições de telemóvel (mobile.mjs); 4. pára o servidor.
// Uso: npm run build && npm run test:e2e        (E2E_SKIP_BUILD não existe: o build é explícito)
import { spawn, spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import postgres from "postgres";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const host = process.env.EDITORIAL_TEST_PG ?? "127.0.0.1:55432";
const db = process.env.E2E_DB ?? "editorial_e2e";
if (!/^[a-z_][a-z0-9_]*$/.test(db) || ["editorial", "editorial_dev", "postgres"].includes(db)) throw new Error(`E2E_DB recusado: ${db}`);
const port = process.env.E2E_PORT ?? "3100";
const owner = `postgres://postgres:postgres@${host}/${db}`;
const admin = { email: "direcao@exemplo.invalid", password: "redacao-local-123" };

const pg = postgres(`postgres://postgres:postgres@${host}/postgres`, { max: 1, onnotice: () => {} });
await pg.unsafe(`drop database if exists ${db} with (force)`);
await pg.unsafe(`create database ${db}`);
await pg.end();

const run = (cmd, args, env = {}) => {
  const r = spawnSync(cmd, args, { cwd: root, stdio: "inherit", env: { ...process.env, ...env } });
  if (r.status !== 0) throw new Error(`${cmd} ${args.join(" ")} falhou`);
};
run("node", ["db/migrate.mjs"], { EDITORIAL_MIGRATION_URL: owner });
const o = postgres(owner, { max: 1, onnotice: () => {} });
await o.unsafe("alter role editorial_app login password 'app_local'");
await o.end();
run("node", ["db/seed.mjs"], { EDITORIAL_MIGRATION_URL: owner, EDITORIAL_SEED_FILE: "config/seed.example.json",
  EDITORIAL_ADMIN_EMAIL: admin.email, EDITORIAL_ADMIN_PASSWORD: admin.password });

const server = spawn("npx", ["next", "start", "-p", port, "-H", "127.0.0.1"], {
  cwd: root, stdio: ["ignore", "pipe", "inherit"], detached: true,
  env: { ...process.env, EDITORIAL_DATABASE_URL: `postgres://editorial_app:app_local@${host}/${db}`,
    EDITORIAL_DEFAULT_PUBLICATION: "gazeta-exemplo", EDITORIAL_SITE_URL: `http://127.0.0.1:${port}` },
});
const base = `http://127.0.0.1:${port}`;
let failed = false;
try {
  for (let i = 0; i < 60; i++) {
    try { if ((await fetch(`${base}/redacao/entrar`)).ok) break; } catch { /* ainda a arrancar */ }
    await new Promise((r) => setTimeout(r, 500));
  }
  const env = { E2E_BASE_URL: base, E2E_ADMIN_EMAIL: admin.email, E2E_ADMIN_PASSWORD: admin.password };
  for (const script of process.argv.slice(2).length ? process.argv.slice(2) : ["run.mjs", "mobile.mjs"]) {
    console.log(`\n=== ${script} ===`);
    const r = spawnSync("node", [join("tests", "e2e", script)], { cwd: root, stdio: "inherit", env: { ...process.env, ...env } });
    if (r.status !== 0) failed = true;
  }
} finally {
  try { process.kill(-server.pid, "SIGTERM"); } catch { /* já parou */ }
}
process.exit(failed ? 1 : 0);
