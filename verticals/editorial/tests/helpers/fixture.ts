import { randomBytes } from "node:crypto";
import postgres from "postgres";
import { type Ctx, humanCtx, type Role } from "@/lib/context";
import { hashPassword } from "@/lib/password";

let owner: postgres.Sql | undefined;
/** Ligação do DONO do esquema: só para montar o cenário e para verificar o que a aplicação não consegue ver. */
export function ownerDb(): postgres.Sql {
  owner ??= postgres(process.env.EDITORIAL_TEST_OWNER_URL!, { max: 2, onnotice: () => {}, connection: { search_path: "editorial, public" } });
  return owner;
}
export async function closeOwner() { await owner?.end(); owner = undefined; }

export interface Newsroom {
  publicationId: string;
  slug: string;
  sectionId: string;
  users: Record<string, { id: string; email: string; role: Role }>;
  as: (who: string) => Ctx;
}

let cachedHash: string | undefined;
export const PASSWORD = "palavra-passe-de-teste";

/** Uma redacção completa e isolada: publicação, editoria e uma pessoa por papel (mais um 2.º jornalista). */
export async function newsroom(settings: Record<string, unknown> = {}): Promise<Newsroom> {
  const sql = ownerDb();
  const tag = randomBytes(4).toString("hex");
  const slug = `pub-${tag}`;
  cachedHash ??= await hashPassword(PASSWORD);
  const [pub] = await sql<{ id: string }[]>`
    insert into publications (slug, name, settings) values (${slug}, ${`Publicação ${tag}`},
      ${sql.json({ require_second_reviewer: true, ...settings })}) returning id`;
  const [sec] = await sql<{ id: string }[]>`
    insert into sections (publication_id, slug, name) values (${pub!.id}, 'local', 'Local') returning id`;
  const users: Newsroom["users"] = {};
  const people: [string, Role][] = [["admin", "admin"], ["director", "director"], ["editor", "editor"],
    ["journalist", "journalist"], ["journalist2", "journalist"], ["contributor", "contributor"], ["reviewer", "reviewer"]];
  for (const [key, role] of people) {
    const email = `${key}-${tag}@exemplo.test`;
    const [u] = await sql<{ id: string }[]>`
      insert into users (email, name, password_hash) values (${email}, ${`Pessoa ${key}`}, ${cachedHash}) returning id`;
    await sql`insert into memberships (publication_id, user_id, role, author_slug, display_name)
              values (${pub!.id}, ${u!.id}, ${role}, ${key}, ${`Pessoa ${key}`})`;
    users[key] = { id: u!.id, email, role };
  }
  return {
    publicationId: pub!.id, slug, sectionId: sec!.id, users,
    as: (who) => humanCtx(pub!.id, users[who]!.id, users[who]!.role, `Pessoa ${who}`),
  };
}
