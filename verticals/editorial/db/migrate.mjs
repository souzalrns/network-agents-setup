// Aplica as migrações em ordem, cada uma numa transacção. Usa a ligação do DONO do esquema
// (EDITORIAL_MIGRATION_URL), nunca a da aplicação.
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import postgres from "postgres";

const url = process.env.EDITORIAL_MIGRATION_URL;
if (!url) {
  console.error("Falta EDITORIAL_MIGRATION_URL (ligação do dono do esquema).");
  process.exit(1);
}
const dir = join(dirname(fileURLToPath(import.meta.url)), "migrations");
const sql = postgres(url, { max: 1, onnotice: () => {} });
try {
  await sql`create schema if not exists editorial`;
  await sql`create table if not exists editorial.schema_migrations (name text primary key, applied_at timestamptz not null default now())`;
  const done = new Set((await sql`select name from editorial.schema_migrations`).map((r) => r.name));
  for (const file of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) {
    if (done.has(file)) continue;
    await sql.begin(async (tx) => {
      await tx.unsafe(readFileSync(join(dir, file), "utf8"));
      await tx`insert into editorial.schema_migrations (name) values (${file})`;
    });
    console.log("aplicada:", file);
  }
  console.log("migrações em dia");
} finally {
  await sql.end();
}
