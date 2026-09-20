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

/**
 * Escapa uma string para uso seguro dentro de uma célula de tabela Markdown.
 * A ordem importa: escapar a barra invertida PRIMEIRO, senão um `\` que já
 * exista no texto interfere com o escaping do `|` feito a seguir (achado
 * CodeQL #6, js/incomplete-sanitization).
 */
function escapeMdCell(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/\|/g, '\\|');
}

/**
 * Extrai as strings dos objectos literais de topo de nível de um array
 * `[ {...}, {...} ]` -- contagem de chavetas balanceada, não regex lazy.
 *
 * F1 (2026-09-20) introduziu campos com objectos aninhados (`profile: {...}`)
 * dentro de um agente -- a regex lazy antiga (`[\s\S]*?\}`) parava no
 * primeiro `}` que encontrasse (o do aninhado), truncando ou perdendo o
 * bloco. Comentários `//` antes do `id:` (também introduzidos pelo F1) eram
 * um segundo problema: a regex exigia `id:` logo a seguir a `{`. Esta versão
 * ignora ambos: percorre carácter a carácter, ignora chavetas dentro de
 * strings, e só corta o bloco quando a profundidade volta a 0.
 */
function splitTopLevelBlocks(source: string): string[] {
  // Não usar o primeiro `[` do ficheiro -- `AgentConfig[]` (anotação de tipo)
  // aparece antes do array literal e tem o seu próprio `[]` vazio, que faria
  // o scan terminar de imediato. `=` seguido de `[` é o array real.
  const arrayMatch = source.match(/=\s*\[/);
  const arrayStart = arrayMatch ? arrayMatch.index! + arrayMatch[0].length - 1 : -1;
  if (arrayStart === -1) return [];
  const blocks: string[] = [];
  let depth = 0;
  let blockStart = -1;
  let inString: '"' | "'" | '`' | null = null;
  for (let i = arrayStart; i < source.length; i++) {
    const ch = source[i];
    const prev = source[i - 1];
    if (inString) {
      if (ch === inString && prev !== '\\') inString = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      inString = ch;
      continue;
    }
    if (ch === '{') {
      if (depth === 0) blockStart = i;
      depth++;
    } else if (ch === '}') {
      depth--;
      if (depth === 0 && blockStart !== -1) {
        blocks.push(source.slice(blockStart, i + 1));
        blockStart = -1;
      }
    } else if (ch === ']' && depth === 0) {
      break;
    }
  }
  return blocks;
}

function parseAgents(source: string): AgentRow[] {
  const agents: AgentRow[] = [];
  for (const block of splitTopLevelBlocks(source)) {
    const id = block.match(/id:\s*['"]([^'"]+)['"]/)?.[1];
    if (!id) continue;
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
      md += `| \`${a.id}\` | ${a.visibility} | ${a.domain || '—'} | ${escapeMdCell(a.description)} |\n`;
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

export { generate, parseAgents, escapeMdCell };
