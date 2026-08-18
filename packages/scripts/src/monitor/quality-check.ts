// scripts/monitor/quality-check.ts
//
// NOTA DE FIDELIDADE: este arquivo NÃO veio no material colado pelo usuário — só
// apareceu na árvore de diretórios da "Fase 5 — Pipeline Contínuo" ("scripts/monitor/
// quality-check.ts"), sem código nem descrição de comportamento além do nome. Foi escrito
// combinando as duas peças que a "Fase 4 — Validação" do plano original já definia
// (completude via check-completeness.ts e teste funcional via test-agents.ts) num único
// relatório de saúde, para dar um alvo real a `ingestion-schedule.ts`'s verificação
// "a cada 6 horas" (que hoje só chama checkCompleteness diretamente — este script é uma
// alternativa mais completa, chamável isoladamente via `pnpm monitor:quality`).

import { checkCompleteness } from '../validate/check-completeness';
import { bootstrap } from '../bootstrap';

const MIN_OPERATIONAL_RATIO = 0.5; // pelo menos metade dos agentes jurídicos operacionais
const MAX_RESPONSE_TIME_MS = 3000; // meta de <3s definida na tabela de critérios de sucesso do plano

export interface QualityReport {
  timestamp: Date;
  operationalAgents: number;
  totalAgents: number;
  averageCompleteness: number;
  sampleQuery: { query: string; durationMs: number; ok: boolean } | null;
  alerts: string[];
}

export async function checkQuality(): Promise<QualityReport> {
  const alerts: string[] = [];

  console.log('🔍 VERIFICAÇÃO DE QUALIDADE');
  console.log('='.repeat(60));

  const results = await checkCompleteness();
  const operationalAgents = results.filter((r) => r.status === 'operational').length;
  const averageCompleteness =
    results.length > 0 ? results.reduce((sum, r) => sum + r.completeness, 0) / results.length : 0;

  if (results.length > 0 && operationalAgents / results.length < MIN_OPERATIONAL_RATIO) {
    alerts.push(
      `Apenas ${operationalAgents}/${results.length} agentes jurídicos operacionais (mínimo esperado: ${Math.round(MIN_OPERATIONAL_RATIO * 100)}%).`
    );
  }

  // Amostra de latência: uma consulta real via Orchestrator, para acompanhar o critério
  // de sucesso "<3s response time" do plano original.
  let sampleQuery: QualityReport['sampleQuery'] = null;
  try {
    const { orchestrator } = bootstrap();
    const query = 'Qual o prazo para contestar uma ação trabalhista?';
    const start = Date.now();
    const result = await orchestrator.processRequest(query, { domain: 'legal', context: { jurisdiction: 'BR' } });
    const durationMs = Date.now() - start;
    const ok = Boolean(result.content) && durationMs <= MAX_RESPONSE_TIME_MS;
    sampleQuery = { query, durationMs, ok };

    if (durationMs > MAX_RESPONSE_TIME_MS) {
      alerts.push(`Consulta de amostra levou ${durationMs}ms (meta: <${MAX_RESPONSE_TIME_MS}ms).`);
    }
  } catch (error: any) {
    alerts.push(`Consulta de amostra falhou: ${error.message}`);
  }

  console.log(`\n📊 Completude média: ${averageCompleteness.toFixed(1)}%`);
  console.log(`📊 Agentes operacionais: ${operationalAgents}/${results.length}`);
  if (sampleQuery) {
    console.log(`📊 Latência de amostra: ${sampleQuery.durationMs}ms (${sampleQuery.ok ? '✅' : '⚠️'})`);
  }

  if (alerts.length > 0) {
    console.log('\n⚠️ ALERTAS:');
    alerts.forEach((a) => console.log(`  - ${a}`));
  } else {
    console.log('\n✅ Nenhum alerta.');
  }

  return {
    timestamp: new Date(),
    operationalAgents,
    totalAgents: results.length,
    averageCompleteness,
    sampleQuery,
    alerts,
  };
}

if (require.main === module) {
  checkQuality()
    .then((report) => process.exit(report.alerts.length > 0 ? 1 : 0))
    .catch((error) => {
      console.error('❌ Erro na verificação de qualidade:', error);
      process.exit(1);
    });
}
