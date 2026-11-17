import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import postgres from "postgres";

/** Cria uma base de dados de teste limpa e aplica as migrações reais (as mesmas de produção). */
export default async function setup() {
  const host = process.env.EDITORIAL_TEST_PG ?? "127.0.0.1:55432";
  const name = process.env.EDITORIAL_TEST_DB ?? "editorial_test";
  if (!/^[a-z_][a-z0-9_]*$/.test(name)) throw new Error("EDITORIAL_TEST_DB inválido");
  const admin = postgres(`postgres://postgres:postgres@${host}/postgres`, { max: 1, onnotice: () => {} });
  await admin.unsafe(`drop database if exists ${name} with (force)`);
  await admin.unsafe(`create database ${name}`);
  await admin.end();
  const owner = postgres(`postgres://postgres:postgres@${host}/${name}`, { max: 1, onnotice: () => {} });
  const dir = join(process.cwd(), "db", "migrations");
  for (const f of readdirSync(dir).filter((x) => x.endsWith(".sql")).sort()) {
    await owner.unsafe(readFileSync(join(dir, f), "utf8"));
  }
  await owner.unsafe("alter role editorial_app login password 'app_local'");
  await owner.end();
}
