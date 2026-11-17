import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { agentCtx, publicCtx, systemCtx } from "@/lib/context";
import { closeDb, db, withCtx } from "@/lib/db";
import { createStory } from "@/lib/stories";
import { closeOwner, type Newsroom, newsroom, ownerDb } from "./helpers/fixture";

let A: Newsroom, B: Newsroom;
let storyA: string, storyB: string;

beforeAll(async () => {
  [A, B] = [await newsroom(), await newsroom()];
  storyA = (await createStory(A.as("journalist"), { title: "Peça da publicação A", sectionId: A.sectionId })).id;
  storyB = (await createStory(B.as("journalist"), { title: "Peça da publicação B", sectionId: B.sectionId })).id;
  for (const [n, s] of [[A, storyA], [B, storyB]] as const) {
    await withCtx(n.as("journalist"), async (tx) => {
      await tx`insert into sources (publication_id, name, contact, owner_id) values (${n.publicationId}, 'Fonte', 'contacto reservado', ${n.users.journalist!.id})`;
      await tx`insert into comments (publication_id, story_id, author_id, body) values (${n.publicationId}, ${s}, ${n.users.journalist!.id}, 'nota interna')`;
    });
  }
});
afterAll(async () => { await closeDb(); await closeOwner(); });

const TABLES = ["publications", "memberships", "sections", "stories", "story_events", "story_versions", "comments", "sources"];

describe("isolamento entre publicações", () => {
  it("sem contexto de transacção a aplicação não vê nenhuma linha", async () => {
    for (const t of TABLES) {
      const rows = await db().unsafe(`select 1 from editorial.${t}`);
      expect(rows.length, t).toBe(0);
    }
    expect((await ownerDb()`select count(*)::int as n from stories`)[0]!.n).toBeGreaterThanOrEqual(2);
  });

  it("cada redacção só vê as suas linhas, em todas as tabelas", async () => {
    await withCtx(A.as("director"), async (tx) => {
      for (const t of TABLES) {
        const col = t === "publications" ? "id" : "publication_id";
        const rows = await tx.unsafe<{ p: string }[]>(`select distinct ${col} as p from ${t}`);
        expect(rows.map((r) => r.p), t).toEqual([A.publicationId]);
      }
      expect((await tx`select 1 from stories where id = ${storyB}`).length).toBe(0);
      expect((await tx`select 1 from users where id = ${B.users.journalist!.id}`).length).toBe(0);
    });
  });

  it("não se escreve na publicação de outros: inserir, alterar e apagar não têm efeito", async () => {
    await expect(withCtx(A.as("director"), (tx) =>
      tx`insert into stories (publication_id, title, created_by) values (${B.publicationId}, 'intrusa', ${A.users.director!.id})`,
    )).rejects.toMatchObject({ code: "42501" });
    await withCtx(A.as("admin"), async (tx) => {
      expect((await tx`update stories set title = 'alterada' where id = ${storyB} returning id`).length).toBe(0);
      expect((await tx`delete from stories where id = ${storyB} returning id`).length).toBe(0);
      expect((await tx`update publications set name = 'tomada' where id = ${B.publicationId} returning id`).length).toBe(0);
    });
    const [row] = await ownerDb()`select title from stories where id = ${storyB}`;
    expect(row!.title).toBe("Peça da publicação B");
  });

  it("um utilizador de A com o id da publicação B no contexto não ganha um papel que não tem", async () => {
    // o contexto vem da sessão (auth_session_get junta a pertença); aqui prova-se a segunda linha de defesa:
    // quem não é da direcção de B não lê a auditoria nem gere a equipa de B, mesmo que o contexto fosse forjado
    const forjado = { publicationId: B.publicationId, kind: "human" as const, userId: A.users.journalist!.id, role: "journalist" as const };
    await withCtx(forjado, async (tx) => {
      expect((await tx`select 1 from audit_log`).length).toBe(0);
    });
    await expect(withCtx(forjado, (tx) => tx`insert into memberships (publication_id, user_id, role, author_slug)
      values (${B.publicationId}, ${A.users.journalist!.id}, 'admin', 'intruso')`)).rejects.toMatchObject({ code: "42501" });
  });

  it("um papel inventado não dá acesso de equipa", async () => {
    await withCtx({ publicationId: A.publicationId, kind: "human", userId: A.users.journalist!.id, role: "superuser" as never }, async (tx) => {
      expect((await tx`select 1 from audit_log`).length).toBe(0);
      expect((await tx`update publications set name = 'x' returning id`).length).toBe(0);
    });
  });
});

describe("o que o público, os agentes e o sistema vêem", () => {
  it("o público só vê peças publicadas e nunca fontes, comentários, histórico ou equipa interna", async () => {
    await withCtx(publicCtx(A.publicationId), async (tx) => {
      expect((await tx`select 1 from stories`).length).toBe(0);
      for (const t of ["sources", "story_sources", "comments", "story_events", "story_versions", "claims", "agent_outputs",
        "feed_items", "feed_sources", "audit_log", "distribution_items", "users"]) {
        expect((await tx.unsafe(`select 1 from ${t}`)).length, t).toBe(0);
      }
    });
    await expect(withCtx(publicCtx(A.publicationId), (tx) =>
      tx`insert into stories (publication_id, title) values (${A.publicationId}, 'do público')`)).rejects.toMatchObject({ code: "42501" });
  });

  it("um agente não lê fontes nem comentários e não altera peças", async () => {
    const agent = agentCtx(A.publicationId, "editorial.research");
    await withCtx(agent, async (tx) => {
      expect((await tx`select 1 from stories where id = ${storyA}`).length).toBe(1); // precisa do contexto da peça
      for (const t of ["sources", "story_sources", "comments", "audit_log", "users", "story_events"]) {
        expect((await tx.unsafe(`select 1 from ${t}`)).length, t).toBe(0);
      }
      expect((await tx`update stories set title = 'reescrita pelo agente' where id = ${storyA} returning id`).length).toBe(0);
      expect((await tx`delete from stories where id = ${storyA} returning id`).length).toBe(0);
    });
    expect((await ownerDb()`select title from stories where id = ${storyA}`)[0]!.title).toBe("Peça da publicação A");
  });

  it("um agente cria ideias, e só ideias, sem dono nem responsável", async () => {
    const agent = agentCtx(A.publicationId, "editorial.radar");
    const idea = await createStory(agent, { title: "Sugestão do radar", propose: true });
    expect(idea.state).toBe("idea");
    expect(idea.origin).toBe("agent");
    await expect(withCtx(agent, (tx) =>
      tx`insert into stories (publication_id, title, state, origin) values (${A.publicationId}, 'já aprovada', 'pitch_approved', 'agent')`,
    )).rejects.toMatchObject({ code: "42501" });
    await expect(withCtx(agent, (tx) =>
      tx`insert into stories (publication_id, title, origin, assignee_id) values (${A.publicationId}, 'atribuída', 'agent', ${A.users.journalist!.id})`,
    )).rejects.toMatchObject({ code: "42501" });
  });

  it("o sistema não escreve fontes nem altera peças que não estejam agendadas", async () => {
    await withCtx(systemCtx(A.publicationId), async (tx) => {
      expect((await tx`select 1 from sources`).length).toBe(0);
      expect((await tx`update stories set state = 'published' where id = ${storyA} returning id`).length).toBe(0);
    });
  });
});
