// scripts/docs/generate-code-map.ts
//
// Gera docs/generated/CODE_MAP.md a partir da árvore real do repo.
// Documentação automática de código: packages, entrypoints, scripts npm.
// Não inventa estado — só descreve o que existe no filesystem.

import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(__dirname, '../../../..');
const OUT_DIR = path.join(ROOT, 'docs/generated');
const OUT_FILE = path.join(OUT_DIR, 'CODE_MAP.md');

const SKIP_DIRS = new Set([
  'node_modules',
  '.git',
  'dist',
  'build',
  '.next',
  'coverage',
  '.turbo',
]);

function listPackages(): Array<{ name: string; path: string; description?: string; scripts: string[] }> {
  const packagesDir = path.join(ROOT, 'packages');
  const appsDir = path.join(ROOT, 'apps');
  const results: Array<{ name: string; path: string; description?: string; scripts: string[] }> = [];

  for (const base of [packagesDir, appsDir]) {
    if (!fs.existsSync(base)) continue;
    for (const name of fs.readdirSync(base)) {
      const pkgPath = path.join(base, name);
      const pkgJsonPath = path.join(pkgPath, 'package.json');
      if (!fs.existsSync(pkgJsonPath)) continue;
      const pkg = JSON.parse(fs.readFileSync(pkgJsonPath, 'utf8'));
      results.push({
        name: pkg.name || name,
        path: path.relative(ROOT, pkgPath),
        description: pkg.description,
        scripts: Object.keys(pkg.scripts || {}),
      });
    }
  }
  return results.sort((a, b) => a.path.localeCompare(b.path));
}

function findEntrypoints(relDir: string, maxDepth = 3): string[] {
  const abs = path.join(ROOT, relDir);
  if (!fs.existsSync(abs)) return [];
  const found: string[] = [];

  function walk(dir: string, depth: number) {
    if (depth > maxDepth) return;
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      if (SKIP_DIRS.has(e.name)) continue;
      const full = path.join(dir, e.name);
      if (e.isDirectory()) {
        walk(full, depth + 1);
      } else if (/^(index|main|server|Orchestrator|AgentFactory)\.(ts|js|tsx)$/.test(e.name)) {
        found.push(path.relative(ROOT, full));
      }
    }
  }
  walk(abs, 0);
  return found.sort();
}

function topLevelTree(): string[] {
  const lines: string[] = [];
  const entries = fs.readdirSync(ROOT, { withFileTypes: true });
  for (const e of entries) {
    if (SKIP_DIRS.has(e.name) || e.name.startsWith('.')) continue;
    lines.push(e.isDirectory() ? `${e.name}/` : e.name);
  }
  return lines.sort();
}

function generate(): string {
  const now = new Date().toISOString().slice(0, 10);
  const packages = listPackages();
  const rootPkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));

  let md = `# CODE_MAP — gerado automaticamente

> **Não editar à mão.** Regenerar com:
> \`pnpm --filter @network-agents/scripts docs:code-map\`
>
> Gerado em: ${now}
> Repo: ${rootPkg.name || 'network-agents'} @ ${rootPkg.version || '?'}

## Árvore de topo

\`\`\`
${topLevelTree().join('\n')}
\`\`\`

## Packages e apps

| Package | Path | Scripts |
|---------|------|---------|
`;

  for (const p of packages) {
    const scripts = p.scripts.length ? p.scripts.join(', ') : '—';
    md += `| \`${p.name}\` | \`${p.path}\` | ${scripts} |\n`;
  }

  md += `\n## Entrypoints detectados\n\n`;
  for (const p of packages) {
    const entries = findEntrypoints(p.path);
    if (entries.length === 0) continue;
    md += `### ${p.name}\n\n`;
    for (const e of entries) {
      md += `- \`${e}\`\n`;
    }
    md += '\n';
  }

  md += `## Scripts de documentação e validação\n\n`;
  const scriptsPkg = packages.find((p) => p.path.includes('scripts'));
  if (scriptsPkg) {
    for (const s of scriptsPkg.scripts) {
      md += `- \`pnpm --filter ${scriptsPkg.name} ${s}\`\n`;
    }
  }

  md += `\n---\n*Mapa gerado a partir do filesystem — não substitui docs/STATUS.md.*\n`;
  return md;
}

function main() {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  const md = generate();
  fs.writeFileSync(OUT_FILE, md, 'utf8');
  console.log(`✅ Escrito ${path.relative(ROOT, OUT_FILE)}`);
}

if (require.main === module) {
  main();
}

export { generate };
