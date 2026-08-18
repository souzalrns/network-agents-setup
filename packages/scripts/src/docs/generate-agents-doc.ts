// scripts/docs/generate-agents-doc.ts
//
// Lê config/agents.config.ts e gera docs/generated/AGENTS.md
// Documentação automática da catálogo de agentes (camada, visibilidade, domínio).

import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(__dirname, '../../../..');
const CONFIG = path.join(ROOT, 'config/agents.config.ts');
const OUT_DIR = path.join(ROOT, 'docs/generated');
const OUT_FILE = path.join(OUT_DIR, 'AGENTS.md');

interface AgentRow {
  id: string;
  layer: string;
  visibility: string;
  domain?: string;
  description: string;
}

function parseAgents(source: string): AgentRow[] {
  const agents: AgentRow[] = [];
  // Blocos { id: '...', ... }
  const blockRe = /\{\s*id:\s*['"]([^'"]+)['"][\s\S]*?\}/g;
  let m: RegExpExecArray | null;
  while ((m = blockRe.exec(source)) !== null) {
    const block = m[0];
    const id = m[1];
    const layer = block.match(/layer:\s*['"]([^'"]+)['"]/)?.[1] || '?';
    const visibility = block.match(/visibility:\s*['"]([^'"]+)['"]/)?.[1] || '?';
    const domain = block.match(/domain:\s*['"]([^'"]+)['"]/)?.[1];
    const description =
      block.match(/description:\s*['"]([^'"]+)['"]/)?.[1] ||
      block.match(/description:\s*`([^`]*)`/)?.[1] ||
      '';
    agents.push({ id, layer, visibility, domain, description });
  }
  return agents;
}

function generate(): string {
  const now = new Date().toISOString().slice(0, 10);
  if (!fs.existsSync(CONFIG)) {
    return `# AGENTS — gerado automaticamente\n\n> Config não encontrada: config/agents.config.ts\n`;
  }

  const source = fs.readFileSync(CONFIG, 'utf8');
  const agents = parseAgents(source);

  const byLayer: Record<string, AgentRow[]> = {};
  for (const a of agents) {
    (byLayer[a.layer] ||= []).push(a);
  }

  let md = `# AGENTS — catálogo gerado automaticamente

> **Não editar à mão.** Regenerar com:
> \`pnpm --filter @network-agents/scripts docs:agents\`
>
> Gerado em: ${now}
> Fonte: \`config/agents.config.ts\`
> Total: **${agents.length}** agentes

## Resumo por camada

| Camada | Quantidade |
|--------|------------:|
`;

  for (const layer of Object.keys(byLayer).sort()) {
    md += `| ${layer} | ${byLayer[layer].length} |\n`;
  }

  md += `\n## Por visibilidade\n\n`;
  const pub = agents.filter((a) => a.visibility === 'public').length;
  const priv = agents.filter((a) => a.visibility === 'private').length;
  md += `- **public**: ${pub}\n- **private**: ${priv}\n\n`;

  for (const layer of Object.keys(byLayer).sort()) {
    md += `## Camada \`${layer}\`\n\n`;
    md += `| ID | Visibilidade | Domínio | Descrição |\n`;
    md += `|----|--------------|---------|-----------|\n`;
    for (const a of byLayer[layer]) {
      md += `| \`${a.id}\` | ${a.visibility} | ${a.domain || '—'} | ${a.description.replace(/\|/g, '\\|')} |\n`;
    }
    md += '\n';
  }

  md += `---\n*Gerado a partir de agents.config.ts — alinhado com a regra public/private do PCU.*\n`;
  return md;
}

function main() {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  const md = generate();
  fs.writeFileSync(OUT_FILE, md, 'utf8');
  console.log(`✅ Escrito ${path.relative(ROOT, OUT_FILE)} (${parseAgents(fs.readFileSync(CONFIG, 'utf8')).length} agentes)`);
}

if (require.main === module) {
  main();
}

export { generate, parseAgents };
