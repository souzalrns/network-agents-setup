// Validação da configuração inicial: o exemplo neutro e, se o repositório estiver ao lado, a sementeira real da
// primeira publicação (vive no agent-network-mcp, fora deste repositório público).
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
// @ts-expect-error módulo JavaScript sem tipos
import { validateSeed } from "../db/validate-seed.mjs";

const read = (p: string) => JSON.parse(readFileSync(p, "utf8"));
const v = (s: unknown) => validateSeed(s) as { errors: string[]; warnings: string[] };
const example = () => read(join(process.cwd(), "config", "seed.example.json"));

describe("validação da sementeira", () => {
  it("o exemplo neutro é válido e não traz nenhuma marca real", () => {
    expect(v(example()).errors).toEqual([]);
    expect(JSON.stringify(example()).toLowerCase()).not.toMatch(/o bode|obode/);
  });

  const real = process.env.EDITORIAL_SEED_REAL ?? join(process.cwd(), "..", "..", "..", "agent-network-mcp", "publications", "o-bode", "seed.json");
  it.skipIf(!existsSync(real))("a sementeira da primeira publicação (agent-network-mcp) é válida", () => {
    expect(v(read(real)).errors).toEqual([]);
  });

  it("recusa editoria inexistente, pautas repetidas, cores e endereços inválidos e agentes desconhecidos", () => {
    const s = example();
    s.publication.primary_color = "vermelho";
    s.publication.slug = "Com Espaços";
    s.publication.agent_names = { "editorial.inventado": "X" };
    s.stories = [{ title: "A" , section: "nao-existe" }, { title: "A" }, { title: "B", priority: 7 }];
    s.sections = [...s.sections, { ...s.sections[0] }];
    const { errors } = v(s);
    for (const m of [/primary_color/, /publication.slug/, /agente desconhecido/, /editoria «nao-existe»/, /pauta repetida/, /priority/, /editoria repetida/]) {
      expect(errors.some((e) => m.test(e)), String(m)).toBe(true);
    }
  });

  it("avisa sem bloquear quando os quatro olhos estão desligados ou o site abre à indexação", () => {
    const s = example();
    s.publication.settings = { require_second_reviewer: false };
    s.publication.public_launch = true;
    const r = v(s);
    expect(r.errors).toEqual([]);
    expect(r.warnings.join(" ")).toMatch(/quatro olhos/);
    expect(r.warnings.join(" ")).toMatch(/ERC/);
  });
});
