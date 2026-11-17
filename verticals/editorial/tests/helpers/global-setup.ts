import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import postgres from "postgres";

/** Cria uma base de dados de teste limpa e aplica as migrações reais (as mesmas de produção). */
export default async function setup() {
  const host = process.env.EDITORIAL_TEST_PG ?? "127.0.0.1:55432";
  const admin = postgres(`postgres://postgres:postgres@${host}/postgres`, { max: 1, onnotice: () => {} });
  await admin`drop database if exists editorial_test with (force)`;
  await admin`create database editorial_test`;
  await admin.end();
  const owner = postgres(`postgres://postgres:postgres@${host}/editorial_test`, { max: 1, onnotice: () => {} });
  const dir = join(process.cwd(), "db", "migrations");
  for (const f of readdirSync(dir).filter((x) => x.endsWith(".sql")).sort()) {
    await owner.unsafe(readFileSync(join(dir, f), "utf8"));
  }
  await owner.unsafe("alter role editorial_app login password 'app_local'");
  await owner.end();
}
