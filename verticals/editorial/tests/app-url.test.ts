// A aplicação liga SEMPRE como editorial_app, nunca como dono, mesmo quando só existe a ligação do dono (Neon).
import { describe, expect, it } from "vitest";
// @ts-expect-error módulo JavaScript sem tipos
import { appDatabaseUrl, derivedAppPassword, ownerDatabaseUrl } from "../db/app-url.mjs";

const owner = "postgres://dono:segredo-do-dono@ep-exemplo.eu-central-1.aws.neon.invalid/neondb?sslmode=require";
const pooled = "postgres://dono:segredo-do-dono@ep-exemplo-pooler.eu-central-1.aws.neon.invalid/neondb?sslmode=require";

describe("ligação da aplicação derivada", () => {
  it("usa editorial_app no servidor pooled, com palavra-passe derivada e diferente da do dono", () => {
    const url = new URL(appDatabaseUrl({ DATABASE_URL: pooled, DATABASE_URL_UNPOOLED: owner }));
    expect(url.username).toBe("editorial_app");
    expect(url.hostname).toBe("ep-exemplo-pooler.eu-central-1.aws.neon.invalid");
    expect(url.password).toBe(derivedAppPassword(owner));
    expect(url.password).not.toContain("segredo-do-dono");
    expect(url.searchParams.get("sslmode")).toBe("require");
  });

  it("a configuração explícita ganha; as migrações usam a ligação do dono sem pooler", () => {
    expect(appDatabaseUrl({ EDITORIAL_DATABASE_URL: "postgres://editorial_app:x@h/db", DATABASE_URL: pooled })).toBe("postgres://editorial_app:x@h/db");
    expect(ownerDatabaseUrl({ DATABASE_URL: pooled, DATABASE_URL_UNPOOLED: owner })).toBe(owner);
    expect(appDatabaseUrl({})).toBeUndefined();
  });

  it("a mesma ligação do dono dá sempre a mesma palavra-passe (o build e a aplicação calculam igual)", () => {
    expect(derivedAppPassword(owner)).toBe(derivedAppPassword(owner));
    expect(derivedAppPassword(owner)).not.toBe(derivedAppPassword(owner.replace("segredo", "outro")));
  });
});
