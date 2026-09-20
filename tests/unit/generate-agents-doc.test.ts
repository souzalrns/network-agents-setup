import { describe, it, expect } from 'vitest';
import { escapeMdCell, parseAgents } from '../../packages/scripts/src/docs/generate-agents-doc';

describe('escapeMdCell — CodeQL #6 (js/incomplete-sanitization)', () => {
  it('should escape a plain pipe', () => {
    expect(escapeMdCell('a | b')).toBe('a \\| b');
  });

  it('should escape a lone backslash', () => {
    expect(escapeMdCell('a \\ b')).toBe('a \\\\ b');
  });

  it('should escape backslash-then-pipe without letting the backslash consume the pipe escape', () => {
    // Este é exactamente o caso que a ordem errada (só escapar | primeiro)
    // deixava passar: um "\|" já existente no texto original ficava
    // indistinguível de um "|" escapado por esta função.
    const input = 'literal backslash \\ then a | pipe';
    const output = escapeMdCell(input);
    expect(output).toBe('literal backslash \\\\ then a \\| pipe');
  });

  it('should not alter text with neither backslash nor pipe', () => {
    expect(escapeMdCell('plain text')).toBe('plain text');
  });
});

describe('parseAgents — regressão do F1 (objecto profile aninhado)', () => {
  it('extrai um agente com profile: {...} aninhado sem o perder nem truncar o seguinte', () => {
    // Reproduz exactamente a forma real de civil-law-br/civil-law-pt em
    // config/agents.config.ts depois do F1. A regex lazy antiga
    // (`[\s\S]*?\}`) parava no primeiro `}` -- o do profile aninhado --
    // e perdia o agente (ou corrompia o parsing do seguinte).
    const source = `
export const AGENT_CONFIGS = [
  {
    id: 'civil-law-br',
    layer: 'vertical',
    visibility: 'private',
    domain: 'legal',
    description: 'Direito Civil Brasileiro (contratos, responsabilidade civil, família).',
    systemPrompt: 'Direito Civil {{jurisdiction_label}}.',
    profile: { jurisdiction: 'BR', jurisdiction_label: 'Brasileiro' },
  },
  {
    id: 'civil-law-pt',
    layer: 'vertical',
    visibility: 'private',
    domain: 'legal',
    description: 'Direito Civil Português (contratos, responsabilidade civil, família).',
    systemPrompt: 'Direito Civil {{jurisdiction_label}}.',
    profile: { jurisdiction: 'PT', jurisdiction_label: 'Português' },
  },
];
`;
    const agents = parseAgents(source);
    expect(agents.map((a) => a.id)).toEqual(['civil-law-br', 'civil-law-pt']);
    expect(agents[0].layer).toBe('vertical');
    expect(agents[0].visibility).toBe('private');
    expect(agents[0].domain).toBe('legal');
    expect(agents[1].id).toBe('civil-law-pt');
  });

  it('continua a extrair agentes simples sem profile (não-regressão)', () => {
    const source = `
export const AGENT_CONFIGS = [
  {
    id: 'orchestrator-general',
    layer: 'meta',
    visibility: 'public',
    description: 'Ponto de entrada.',
  },
];
`;
    const agents = parseAgents(source);
    expect(agents).toHaveLength(1);
    expect(agents[0].id).toBe('orchestrator-general');
  });

  it('extrai correctamente os 24 agentes reais de config/agents.config.ts', () => {
    const fs = require('fs');
    const path = require('path');
    const source = fs.readFileSync(path.resolve(__dirname, '../../config/agents.config.ts'), 'utf8');
    const agents = parseAgents(source);
    expect(agents).toHaveLength(24);
    expect(agents.map((a) => a.id)).toContain('civil-law-br');
    expect(agents.map((a) => a.id)).toContain('civil-law-pt');
  });
});
