// scripts/docs/generate-skills-doc.ts
//
// Lê skills/**/SKILL.md e gera docs/generated/SKILLS.md.
// Fecha o S35: hoje a única "descoberta" de skills é a convenção Markdown
// skills/meta/using-agent-skills/SKILL.md (Advisory, zero imposição em
// código) — este gerador dá um catálogo real, análogo ao docs:agents (F6).
//
// Não impõe nada em runtime (continua Advisory) — é só documentação
// gerada, mesmo padrão do generate-agents-doc.ts.

import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(__dirname, '../../../..');
const SKILLS_DIR = path.join(ROOT, 'skills');
const OUT_DIR = path.join(ROOT, 'docs/generated');
const OUT_FILE = path.join(OUT_DIR, 'SKILLS.md');

interface SkillRow {
  /** Caminho relativo à raiz do repo, ex. skills/design/ux_flow/SKILL.md */
  file: string;
  /** 1º segmento depois de skills/ — ex. design, marketing, claude, meta */
  domain: string;
  name: string;
  vertical?: string;
  role?: string;
  priority?: string;
  description: string;
}

/**
 * Escapa uma string para uso seguro dentro de uma célula de tabela Markdown.
 * Mesma ordem do generate-agents-doc.ts (barra invertida primeiro).
 */
function escapeMdCell(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/\|/g, '\\|').replace(/\n/g, ' ');
}

function findSkillFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...findSkillFiles(full));
    } else if (entry.isFile() && entry.name.toUpperCase() === 'SKILL.MD') {
      out.push(full);
    }
  }
  return out;
}

/**
 * Parser mínimo do frontmatter YAML usado nos SKILL.md deste repo.
 * Não é um parser YAML genérico -- só cobre os 2 formatos realmente usados
 * aqui: `key: valor` numa linha, e `key: >-` seguido de linhas indentadas
 * (bloco "folded", junta tudo numa frase só, como o YAML real faria).
 * Um parser completo (biblioteca yaml) seria over-engineering para 67
 * ficheiros com 2 formatos conhecidos.
 */
function parseFrontmatter(source: string): Record<string, string> {
  const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const lines = match[1].split(/\r?\n/);
  const fields: Record<string, string> = {};
  let currentKey: string | null = null;
  let blockLines: string[] = [];

  const flushBlock = () => {
    if (currentKey) fields[currentKey] = blockLines.join(' ').trim();
    currentKey = null;
    blockLines = [];
  };

  for (const line of lines) {
    const blockStart = line.match(/^(\w[\w-]*):\s*[>|]-?\s*$/);
    if (blockStart) {
      flushBlock();
      currentKey = blockStart[1];
      continue;
    }
    if (currentKey) {
      if (/^\s+\S/.test(line)) {
        blockLines.push(line.trim());
        continue;
      }
      flushBlock();
    }
    const kv = line.match(/^(\w[\w-]*):\s*(.*)$/);
    if (kv) {
      const [, key, rawValue] = kv;
      fields[key] = rawValue.trim().replace(/^['"]|['"]$/g, '');
    }
  }
  flushBlock();
  return fields;
}

/** Fallback quando não há `description:` no frontmatter (20/67 skills, ver
 * S35): usa a 1ª linha de texto real do corpo (ignora o H1 e linhas em
 * branco) como resumo curto -- melhor do que ficar vazio na tabela. */
function fallbackDescription(source: string): string {
  const body = source.replace(/^---\r?\n[\s\S]*?\r?\n---/, '');
  const lines = body.split(/\r?\n/);
  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    return line.replace(/^[-*]\s*/, '');
  }
  return '';
}

function parseSkill(file: string): SkillRow | null {
  const rel = path.relative(ROOT, file).split(path.sep).join('/');
  const domain = rel.split('/')[1] ?? '?';
  const source = fs.readFileSync(file, 'utf8');
  const fm = parseFrontmatter(source);
  if (!fm.name) return null;
  return {
    file: rel,
    domain,
    name: fm.name,
    vertical: fm.vertical,
    role: fm.role,
    priority: fm.priority,
    description: fm.description || fallbackDescription(source),
  };
}

function generate(): string {
  const now = new Date().toISOString().slice(0, 10);
  if (!fs.existsSync(SKILLS_DIR)) {
    return `# SKILLS — gerado automaticamente\n\n> Pasta não encontrada: skills/\n`;
  }

  const files = findSkillFiles(SKILLS_DIR).sort();
  const skills = files.map(parseSkill).filter((s): s is SkillRow => s !== null);
  const skipped = files.length - skills.length;

  const byDomain: Record<string, SkillRow[]> = {};
  for (const s of skills) {
    (byDomain[s.domain] ||= []).push(s);
  }

  let md = `# SKILLS — catálogo gerado automaticamente

> **Não editar à mão.** Regenerar com:
> \`pnpm --filter @network-agents/scripts docs:skills\`
>
> Gerado em: ${now}
> Fonte: \`skills/**/SKILL.md\`
> Total: **${skills.length}** skills${skipped ? ` (${skipped} ficheiro(s) sem \`name:\` no frontmatter, ignorado(s))` : ''}
>
> **Nota (S35):** este catálogo é só documentação — a descoberta em runtime
> continua Advisory (\`skills/meta/using-agent-skills/SKILL.md\`), nada aqui
> impõe o mapa de invocação em código.

## Resumo por domínio

| Domínio | Quantidade |
|---------|------------:|
`;

  for (const domain of Object.keys(byDomain).sort()) {
    md += `| ${domain} | ${byDomain[domain].length} |\n`;
  }

  for (const domain of Object.keys(byDomain).sort()) {
    md += `\n## Domínio \`${domain}\`\n\n`;
    md += `| Nome | Vertical/Role | Prioridade | Descrição | Ficheiro |\n`;
    md += `|------|---------------|:----------:|-----------|----------|\n`;
    for (const s of byDomain[domain].sort((a, b) => a.name.localeCompare(b.name))) {
      const vr = s.vertical || s.role || '—';
      md += `| \`${s.name}\` | ${vr} | ${s.priority || '—'} | ${escapeMdCell(s.description)} | \`${s.file}\` |\n`;
    }
  }

  md += `\n---\n*Gerado a partir de skills/**/SKILL.md — mesmo padrão do docs:agents (F6).*\n`;
  return md;
}

function main() {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  const md = generate();
  fs.writeFileSync(OUT_FILE, md, 'utf8');
  const files = fs.existsSync(SKILLS_DIR) ? findSkillFiles(SKILLS_DIR) : [];
  const count = files.map(parseSkill).filter((s) => s !== null).length;
  console.log(`✅ Escrito ${path.relative(ROOT, OUT_FILE)} (${count} skills)`);
}

if (require.main === module) {
  main();
}

export { generate, parseSkill, parseFrontmatter, escapeMdCell };
