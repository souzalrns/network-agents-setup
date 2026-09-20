import { describe, it, expect } from 'vitest';
import { AgentFactory, resolveAgentPrompt } from '../../packages/core/src/agents/AgentFactory';
import { AGENT_CONFIGS } from '../../config/agents.config';

describe('AgentConfig.profile (F1)', () => {
  it('resolveAgentPrompt() produz saídas distintas e correctas para o mesmo agente, por profile', () => {
    const factory = new AgentFactory({ publicMode: false });
    factory.registerAgent({
      id: 'civil-law',
      layer: 'vertical',
      visibility: 'private',
      domain: 'legal',
      description: 'fallback',
      systemPrompt: 'Direito Civil {{jurisdiction_label}} (contratos, responsabilidade civil, família).',
    });
    const agent = factory.getAgent('civil-law')!;

    const br = resolveAgentPrompt(agent, { jurisdiction: 'BR', jurisdiction_label: 'Brasileiro' });
    const pt = resolveAgentPrompt(agent, { jurisdiction: 'PT', jurisdiction_label: 'Português' });

    expect(br).toBe('Direito Civil Brasileiro (contratos, responsabilidade civil, família).');
    expect(pt).toBe('Direito Civil Português (contratos, responsabilidade civil, família).');
    expect(br).not.toBe(pt);
  });

  it('resolveAgentPrompt() sem profile devolve o template tal como está (não-regressão)', () => {
    const factory = new AgentFactory({ publicMode: false });
    factory.registerAgent({
      id: 'generic-agent',
      layer: 'horizontal',
      visibility: 'public',
      description: 'Agente sem profile',
      systemPrompt: 'Responde de forma genérica.',
    });
    const agent = factory.getAgent('generic-agent')!;

    expect(resolveAgentPrompt(agent)).toBe('Responde de forma genérica.');
  });

  it('registerAgent() propaga profile do AgentConfig para o Agent registado', () => {
    const factory = new AgentFactory({ publicMode: false });
    factory.registerAgent({
      id: 'x',
      layer: 'vertical',
      visibility: 'private',
      domain: 'legal',
      description: 'x',
      profile: { jurisdiction: 'BR' },
    });
    expect(factory.getAgent('x')!.profile).toEqual({ jurisdiction: 'BR' });
  });

  it('civil-law-br e civil-law-pt em config/agents.config.ts têm profile real e resolvem diferente (caso migrado da Fase 2)', () => {
    const br = AGENT_CONFIGS.find((a) => a.id === 'civil-law-br')!;
    const pt = AGENT_CONFIGS.find((a) => a.id === 'civil-law-pt')!;
    expect(br.profile).toEqual({ jurisdiction: 'BR', jurisdiction_label: 'Brasileiro' });
    expect(pt.profile).toEqual({ jurisdiction: 'PT', jurisdiction_label: 'Português' });

    const factory = new AgentFactory({ publicMode: false });
    factory.registerAgent(br);
    factory.registerAgent(pt);
    const outBr = resolveAgentPrompt(factory.getAgent('civil-law-br')!);
    const outPt = resolveAgentPrompt(factory.getAgent('civil-law-pt')!);
    expect(outBr).toContain('Brasileiro');
    expect(outPt).toContain('Português');
    expect(outBr).not.toBe(outPt);
  });

  it('não-regressão: os 24 agentes de AGENT_CONFIGS continuam a registar-se, agentId preservado', () => {
    const factory = new AgentFactory({ publicMode: false });
    AGENT_CONFIGS.forEach((c) => factory.registerAgent(c));
    expect(factory.getAllAgents()).toHaveLength(24);
    expect(factory.getAgent('civil-law-br')).toBeDefined();
    expect(factory.getAgent('civil-law-pt')).toBeDefined();
  });
});
