// Semeia UMA publicação a partir de um ficheiro JSON (a marca vive na configuração, não no código).
// Uso: EDITORIAL_MIGRATION_URL=… EDITORIAL_SEED_FILE=caminho/seed.json EDITORIAL_ADMIN_EMAIL=… EDITORIAL_ADMIN_PASSWORD=… node db/seed.mjs
// Idempotente: actualiza a publicação pelo slug; editorias por slug; páginas e pautas só se ainda não existirem.
import { randomBytes, scrypt as scryptCb } from "node:crypto";
import { readFileSync } from "node:fs";
import { promisify } from "node:util";
import postgres from "postgres";
import { validateSeed } from "./validate-seed.mjs";

const scrypt = promisify(scryptCb);
const need = (k) => {
  const v = process.env[k];
  if (!v) { console.error(`Falta ${k}.`); process.exit(1); }
  return v;
};
const url = need("EDITORIAL_MIGRATION_URL");
const seed = JSON.parse(readFileSync(need("EDITORIAL_SEED_FILE"), "utf8"));
{
  const { errors, warnings } = validateSeed(seed);
  for (const w of warnings) console.log(`aviso: ${w}`);
  if (errors.length) { for (const e of errors) console.error(`ERRO: ${e}`); console.error("Sementeira cancelada: corrige o ficheiro."); process.exit(1); }
  console.log("Sementeira inicial: numa publicação existente só se actualizam nome, slogan, descrição, cores e nomes dos agentes.");
}
const adminEmail = process.env.EDITORIAL_ADMIN_EMAIL;
const adminPassword = process.env.EDITORIAL_ADMIN_PASSWORD;
const adminName = process.env.EDITORIAL_ADMIN_NAME ?? "Direção";

async function hash(pw) {
  if (pw.length < 10) throw new Error("A palavra-passe precisa de pelo menos 10 caracteres.");
  const salt = randomBytes(16);
  const h = await scrypt(pw, salt, 32, { N: 1 << 15, r: 8, p: 1, maxmem: 64 * 1024 * 1024 });
  return `scrypt$32768$8$1$${salt.toString("base64url")}$${h.toString("base64url")}`;
}

function angleOf(s) {
  return [
    s.angle,
    s.instagram && `Instagram: ${s.instagram}`,
    s.youtube && `YouTube e podcast: ${s.youtube}`,
    s.sources?.length && `Fontes a contactar: ${s.sources.join("; ")}`,
  ].filter(Boolean).join("\n\n");
}

const sql = postgres(url, { max: 1, onnotice: () => {}, connection: { search_path: "editorial, public" } });
try {
  await sql.begin(async (tx) => {
    const p = seed.publication;
    const [pub] = await tx`insert into publications ${tx({
      slug: p.slug, name: p.name, tagline: p.tagline ?? "", description: p.description ?? "",
      primary_color: p.primary_color ?? "#16211C", secondary_color: p.secondary_color ?? "#F0B429",
      domain: p.domain ?? null, language: p.language ?? "pt-PT", contact_email: p.contact_email ?? null,
      social_links: tx.json(p.social_links ?? {}), legal: tx.json(p.legal ?? {}), agent_names: tx.json(p.agent_names ?? {}),
      settings: tx.json({ require_second_reviewer: true, ...(p.settings ?? {}) }), public_launch: !!p.public_launch,
    })} on conflict (slug) do update set name = excluded.name, tagline = excluded.tagline, description = excluded.description,
      primary_color = excluded.primary_color, secondary_color = excluded.secondary_color, agent_names = excluded.agent_names,
      updated_at = now() returning id`;
    const pid = pub.id;
    const secIds = {};
    for (const [i, s] of (seed.sections ?? []).entries()) {
      const [row] = await tx`insert into sections (publication_id, slug, name, description, color, position)
        values (${pid}, ${s.slug}, ${s.name}, ${s.description ?? ""}, ${s.color ?? "#7A8480"}, ${i + 1})
        on conflict (publication_id, slug) do update set name = excluded.name, color = excluded.color, description = excluded.description
        returning id`;
      secIds[s.slug] = row.id;
    }
    for (const pg of seed.pages ?? []) {
      await tx`insert into pages (publication_id, slug, title, body, published)
        values (${pid}, ${pg.slug}, ${pg.title}, ${pg.body ?? ""}, ${!!pg.published})
        on conflict (publication_id, slug) do nothing`;
    }
    let adminId = null;
    if (adminEmail && adminPassword) {
      const [u] = await tx`insert into users (email, name, password_hash)
        values (${adminEmail.toLowerCase()}, ${adminName}, ${await hash(adminPassword)})
        on conflict (email) do update set name = users.name returning id`;
      adminId = u.id;
      await tx`insert into memberships (publication_id, user_id, role, author_slug, display_name)
        values (${pid}, ${adminId}, 'admin', ${process.env.EDITORIAL_ADMIN_SLUG ?? "direcao"}, ${adminName})
        on conflict (publication_id, user_id) do nothing`;
    }
    let created = 0;
    for (const s of seed.stories ?? []) {
      const [exists] = await tx`select 1 from stories where publication_id = ${pid} and title = ${s.title}`;
      if (exists) continue;
      await tx`insert into stories (publication_id, section_id, state, priority, format, origin, title, angle, to_confirm, interview_questions, due_date)
        values (${pid}, ${secIds[s.section] ?? null}, 'idea', ${s.priority ?? 2}, ${s.format ?? "reportagem"}, 'human', ${s.title},
          ${angleOf(s)}, ${s.to_confirm ?? ""}, ${s.questions ?? []}, ${s.due_date ?? null})`;
      created++;
    }
    console.log(`publicação ${p.slug} (${pid}): ${Object.keys(secIds).length} editorias, ${(seed.pages ?? []).length} páginas, ${created} pautas novas${adminId ? ", administrador pronto" : ""}`);
  });
} finally {
  await sql.end();
}
