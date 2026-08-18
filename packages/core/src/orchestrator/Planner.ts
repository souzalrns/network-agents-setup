import { AgentFactory } from '../agents/AgentFactory';
import { LLMService } from '../llm/LLMService';
import { Plan } from '@network-agents/shared';
export class Planner {
  constructor(
    _agentFactory: AgentFactory,
    private llm: LLMService
  ) {}
  async plan(
    input: string,
    domainAgents: any[],
    context?: Record<string, any>
  ): Promise<Plan> {
    const agentList = domainAgents
      .map((a) => `- ${a.id}: ${a.description}`)
      .join('\n');
    const prompt = `
      Você é um planejador de tarefas para uma rede de agentes.
      **Domínio:** ${context?.domain || 'geral'}
      **Agentes disponíveis:**
      ${agentList}
      **Tarefa:** ${input}
      **Objetivo:** Criar um plano de execução detalhado, escolhendo os agentes certos e definindo a ordem correta.
      **Instruções:**
      1. Identifique a intenção principal da tarefa.
      2. Escolha os agentes mais adequados para cada subtarefa.
      3. Defina a ordem de execução (dependências).
      4. Para tarefas complexas, divida em passos claros.
      5. Cada passo deve ter um agente responsável e uma descrição clara do que fazer.
      6. Se houver necessidade de revisão/crítica, inclua um agente de validação.
      7. Se houver necessidade de pesquisa, inclua o Research Agent.
      8. Se houver necessidade de aprovação humana, marque o passo com requiresApproval.
      **FORMATO DE SAÍDA (JSON):**
      {
        "intent": "descrição da intenção principal",
        "steps": [
          {
            "id": "step_1",
            "agentId": "id do agente",
            "description": "descrição clara do passo",
            "prompt": "prompt específico para o agente",
            "critical": false,
            "contextKeys": ["chave1", "chave2"],
            "requiresApproval": false,
            "approvalTitle": "Título para aprovação",
            "approvalDescription": "Descrição para aprovação",
            "approvalCategory": "financial|legal|medical|strategic|approval",
            "approvalPriority": "low|medium|high|critical"
          }
        ],
        "finalConsolidator": "id do agente que vai consolidar (opcional)"
      }
    `;
    const response = await this.llm.chat({
      system: 'Você é um planejador de tarefas especializado em orquestrar agentes.',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.2,
    });
    try {
      const jsonMatch = response.content.match(/\{[\s\S]*\}/);
      const planData = JSON.parse(jsonMatch ? jsonMatch[0] : response.content);
      this.validatePlan(planData, domainAgents);
      return {
        id: `plan_${Date.now()}`,
        intent: planData.intent || input,
        domain: context?.domain || 'general',
        steps: planData.steps || [],
        finalConsolidator: planData.finalConsolidator,
        conversationId: context?.conversationId,
        metadata: {
          priority: planData.priority || 'medium',
        },
      };
    } catch (error) {
      return this.fallbackPlan(input, domainAgents);
    }
  }
  private validatePlan(planData: any, domainAgents: any[]): void {
    const availableIds = new Set(domainAgents.map((a) => a.id));
    for (const step of planData.steps || []) {
      if (!availableIds.has(step.agentId)) {
        throw new Error(`Agent ${step.agentId} not available in this domain`);
      }
    }
  }
  private fallbackPlan(input: string, domainAgents: any[]): Plan {
    const defaultAgent = domainAgents[0];
    return {
      id: `plan_fallback_${Date.now()}`,
      intent: input,
      domain: domainAgents[0]?.domain || 'general',
      steps: [
        {
          id: 'step_1',
          agentId: defaultAgent?.id || 'unknown',
          description: `Processar: ${input}`,
          prompt: input,
          critical: true,
        },
      ],
    };
  }
}
