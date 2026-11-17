// Preparação da base de dados durante o build (Vercel: script `vercel-build`). Só corre com EDITORIAL_PROVISION=1:
// sem isso não faz nada, e o build segue normalmente.
// 1. aplica as migrações em falta (db/migrate.mjs) com a ligação do DONO;
// 2. deixa o papel editorial_app entrar, com a palavra-passe derivada (db/app-url.mjs);
// 3. semeia a publicação a partir de EDITORIAL_SEED_JSON (o conteúdo do ficheiro) ou EDITORIAL_SEED_FILE,
//    validado antes (db/validate-seed.mjs), com a conta de administração de EDITORIAL_ADMIN_EMAIL/PASSWORD.
// Idempotente: pode correr em todos os builds. Nunca imprime ligações nem palavras-passe.
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import postgres from "postgres";
import { APP_ROLE, derivedAppPassword, ownerDatabaseUrl } from "./app-url.mjs";

if (process.env.EDITORIAL_PROVISION !== "1") {
  console.log("[preparação] EDITORIAL_PROVISION não está a 1: nada a fazer.");
  process.exit(0);
}
const here = dirname(fileURLToPath(import.meta.url));
const owner = ownerDatabaseUrl();
if (!owner) {
  console.error("[preparação] Falta a ligação do dono (EDITORIAL_MIGRATION_URL, DATABASE_URL_UNPOOLED ou POSTGRES_URL_NON_POOLING).");
  process.exit(1);
}
const run = (script, env) => {
  const r = spawnSync(process.execPath, [join(here, script)], { stdio: "inherit", env: { ...process.env, ...env } });
  if (r.status !== 0) { console.error(`[preparação] ${script} falhou.`); process.exit(1); }
};

run("migrate.mjs", { EDITORIAL_MIGRATION_URL: owner });

const sql = postgres(owner, { max: 1, onnotice: () => {} });
try {
  // a palavra-passe vai como literal escapado pelo próprio Postgres (format %L): nunca concatenada à mão
  const [{ stmt }] = await sql`select format('alter role %I login password %L', ${APP_ROLE}::text, ${derivedAppPassword(owner)}::text) as stmt`;
  await sql.unsafe(stmt);
  console.log("[preparação] papel editorial_app pronto.");
} finally {
  await sql.end();
}

let seedFile = process.env.EDITORIAL_SEED_FILE;
if (process.env.EDITORIAL_SEED_JSON) {
  seedFile = join(mkdtempSync(join(tmpdir(), "seed-")), "seed.json");
  writeFileSync(seedFile, process.env.EDITORIAL_SEED_JSON);
}
if (seedFile) run("seed.mjs", { EDITORIAL_MIGRATION_URL: owner, EDITORIAL_SEED_FILE: seedFile });
else console.log("[preparação] sem EDITORIAL_SEED_JSON nem EDITORIAL_SEED_FILE: sem sementeira.");
