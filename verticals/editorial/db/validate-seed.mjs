// Validação da configuração inicial de uma publicação (ficheiro de sementeira), antes de tocar na base de dados.
// A sementeira é INICIAL: numa publicação que já existe só actualiza nome, slogan, descrição, cores e nomes
// dos agentes; editorias, páginas e pautas só entram se ainda não existirem. O resto configura-se na redacção.
// Uso: node db/validate-seed.mjs caminho/seed.json [outro.json …]   (sai com 1 se houver erros)
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const HEX = /^#[0-9a-fA-F]{6}$/;
const AGENTS = ["editorial.radar", "editorial.research", "editorial.factcheck", "editorial.editor"];
const LANG = /^[a-z]{2}(-[A-Z]{2})?$/;
const HOST = /^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;
const isObj = (v) => v !== null && typeof v === "object" && !Array.isArray(v);

/** Devolve { errors, warnings }. Erros impedem a sementeira; avisos não. */
export function validateSeed(seed) {
  const errors = [], warnings = [];
  const err = (m) => errors.push(m), warn = (m) => warnings.push(m);
  if (!isObj(seed)) return { errors: ["o ficheiro não é um objecto JSON"], warnings };
  const p = seed.publication;
  if (!isObj(p)) err("falta «publication»");
  else {
    if (typeof p.slug !== "string" || !SLUG.test(p.slug)) err("publication.slug tem de ser minúsculas, números e hífenes");
    if (typeof p.name !== "string" || !p.name.trim()) err("publication.name é obrigatório");
    for (const k of ["primary_color", "secondary_color"]) if (p[k] !== undefined && !HEX.test(p[k])) err(`publication.${k} tem de ser uma cor #RRGGBB`);
    if (p.language !== undefined && !LANG.test(p.language)) err("publication.language tem de ser do tipo pt-PT");
    if (p.domain !== undefined && p.domain !== null && !HOST.test(String(p.domain))) err("publication.domain tem de ser um nome de domínio (sem https://)");
    if (p.contact_email !== undefined && p.contact_email !== null && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(p.contact_email)) err("publication.contact_email inválido");
    if (p.agent_names !== undefined) {
      if (!isObj(p.agent_names)) err("publication.agent_names tem de ser um objecto");
      else for (const [k, v] of Object.entries(p.agent_names)) {
        if (!AGENTS.includes(k)) err(`publication.agent_names: agente desconhecido «${k}» (conhecidos: ${AGENTS.join(", ")})`);
        if (typeof v !== "string" || !v.trim() || v.length > 60) err(`publication.agent_names.${k}: nome entre 1 e 60 caracteres`);
      }
    }
    if (p.social_links !== undefined) {
      if (!isObj(p.social_links)) err("publication.social_links tem de ser um objecto");
      else for (const [k, v] of Object.entries(p.social_links)) if (!/^https?:\/\//.test(String(v))) err(`publication.social_links.${k} tem de ser um endereço http(s)`);
    }
    if (p.settings !== undefined && (!isObj(p.settings) || (p.settings.require_second_reviewer !== undefined && typeof p.settings.require_second_reviewer !== "boolean"))) {
      err("publication.settings.require_second_reviewer tem de ser verdadeiro ou falso");
    }
    if (p.settings?.require_second_reviewer === false) warn("os quatro olhos estão desligados: quem escreve pode aprovar e verificar o próprio trabalho");
    if (p.public_launch) warn("public_launch: verdadeiro abre o site à indexação; confirmar o registo na ERC antes");
  }
  const sections = Array.isArray(seed.sections) ? seed.sections : seed.sections === undefined ? [] : (err("«sections» tem de ser uma lista"), []);
  const secSlugs = new Set();
  sections.forEach((s, i) => {
    if (!isObj(s)) return err(`sections[${i}] não é um objecto`);
    if (typeof s.slug !== "string" || !SLUG.test(s.slug)) err(`sections[${i}].slug inválido`);
    else if (secSlugs.has(s.slug)) err(`editoria repetida: «${s.slug}»`);
    else secSlugs.add(s.slug);
    if (typeof s.name !== "string" || !s.name.trim()) err(`sections[${i}].name é obrigatório`);
    if (s.color !== undefined && !HEX.test(s.color)) err(`sections[${i}].color tem de ser #RRGGBB`);
  });
  if (!sections.length) warn("sem editorias: as pautas ficam por classificar");
  const pages = Array.isArray(seed.pages) ? seed.pages : seed.pages === undefined ? [] : (err("«pages» tem de ser uma lista"), []);
  const pageSlugs = new Set();
  pages.forEach((pg, i) => {
    if (!isObj(pg)) return err(`pages[${i}] não é um objecto`);
    if (typeof pg.slug !== "string" || !SLUG.test(pg.slug)) err(`pages[${i}].slug inválido`);
    else if (pageSlugs.has(pg.slug)) err(`página repetida: «${pg.slug}»`);
    else pageSlugs.add(pg.slug);
    if (typeof pg.title !== "string" || !pg.title.trim()) err(`pages[${i}].title é obrigatório`);
    if (pg.body !== undefined && typeof pg.body !== "string") err(`pages[${i}].body tem de ser texto`);
  });
  for (const must of ["estatuto-editorial", "politica-de-correcoes"]) if (!pageSlugs.has(must)) warn(`falta a página «${must}» (o site liga para ela)`);
  const stories = Array.isArray(seed.stories) ? seed.stories : seed.stories === undefined ? [] : (err("«stories» tem de ser uma lista"), []);
  const titles = new Set();
  stories.forEach((s, i) => {
    if (!isObj(s)) return err(`stories[${i}] não é um objecto`);
    if (typeof s.title !== "string" || !s.title.trim()) return err(`stories[${i}].title é obrigatório`);
    if (s.title.length > 300) err(`stories[${i}].title tem mais de 300 caracteres`);
    if (titles.has(s.title)) err(`pauta repetida (a sementeira ignorá-la-ia em silêncio): «${s.title}»`);
    titles.add(s.title);
    if (s.section !== undefined && !secSlugs.has(s.section)) err(`stories[${i}] («${s.title.slice(0, 40)}»): editoria «${s.section}» não existe em «sections»`);
    if (s.priority !== undefined && ![1, 2, 3].includes(s.priority)) err(`stories[${i}].priority tem de ser 1, 2 ou 3`);
    if (s.due_date !== undefined && s.due_date !== null && !/^\d{4}-\d{2}-\d{2}$/.test(s.due_date)) err(`stories[${i}].due_date tem de ser AAAA-MM-DD`);
    for (const k of ["questions", "sources"]) if (s[k] !== undefined && (!Array.isArray(s[k]) || s[k].some((q) => typeof q !== "string"))) err(`stories[${i}].${k} tem de ser uma lista de textos`);
  });
  const known = new Set(["publication", "sections", "pages", "stories", "$schema", "_comment", "_nota", "notes"]);
  for (const k of Object.keys(seed)) if (!known.has(k)) warn(`campo desconhecido no topo: «${k}» (ignorado)`);
  return { errors, warnings };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const files = process.argv.slice(2);
  if (!files.length) { console.error("Uso: node db/validate-seed.mjs caminho/seed.json …"); process.exit(1); }
  let bad = 0;
  for (const f of files) {
    let seed;
    try { seed = JSON.parse(readFileSync(f, "utf8")); } catch (e) { console.error(`${f}: JSON inválido (${e.message})`); bad++; continue; }
    const { errors, warnings } = validateSeed(seed);
    for (const w of warnings) console.log(`${f}: aviso: ${w}`);
    for (const e of errors) console.error(`${f}: ERRO: ${e}`);
    console.log(`${f}: ${errors.length ? `${errors.length} erros` : "válido"}, ${warnings.length} avisos`);
    if (errors.length) bad++;
  }
  process.exit(bad ? 1 : 0);
}
