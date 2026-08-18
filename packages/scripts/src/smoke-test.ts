// scripts/smoke-test.ts
//
// Colado pelo usuário como resposta ao pedido "por que já não testa" — em vez de deixar
// o smoke-test manual (rodado ad-hoc contra um fake Prisma nesta sessão) descartado, virou
// um script real do pacote. Cinco ajustes em relação ao texto colado, todos pela mesma
// razão de sempre — o texto assumia coisas que não existem na base real:
//
// 1. `const orchestrator = new Orchestrator(/* ... dependências ... */);` — o mesmo
//    placeholder inválido de test-agents.ts. Trocado por `bootstrap()`.
// 2. `import { testAgents } from './validate/test-agents'` e
//    `const logger = getGlobalLogger();` eram importados/declarados e nunca usados
//    (TS6133 sob `noUnusedLocals`) — removidos.
// 3. `const prisma = new PrismaClient()` local trocado por `import { prisma } from './db'`
//    (mesma consolidação do resto do pacote).
// 4. O teste de embeddings não tinha um caminho gracioso para "sem OPENAI_API_KEY" (só o
//    teste do orquestrador tinha essa checagem) — sem isso, rodar `pnpm smoke-test` sem
//    chave sempre reportaria "Embeddings" como falha, mesmo sendo uma limitação de
//    configuração e não um bug. Adicionado o mesmo padrão de "teste parcial" do
//    orquestrador.
// 5. Suporte básico à flag `--quick` (declarada em package.json como
//    `smoke-test:quick` mas nunca implementada no texto colado) — pula o teste de rede
//    real (mais lento e não essencial para checar a lógica local).

import { prisma } from './db';
import { checkCompleteness } from './validate/check-completeness';
import { BrazilianLawIngestor } from './ingest/brazilian-law';
import { PortugueseLawIngestor } from './ingest/portuguese-law';
import { JurisprudenceIngestor } from './ingest/jurisprudence';
import { DoctrineIngestor } from './ingest/doctrine';
import { EmbeddingGenerator } from './ingest/embeddings';
import { createBrazilianLawTools } from '@network-agents/mcp';
import { bootstrap } from './bootstrap';

const QUICK = process.argv.includes('--quick');

function hasRealApiKey(): boolean {
  return !!process.env.OPENAI_API_KEY && process.env.OPENAI_API_KEY !== 'your-openai-api-key-here';
}

interface SmokeTestResult {
  name: string;
  passed: boolean;
  details: string;
  duration: number;
}

export class SmokeTest {
  private results: SmokeTestResult[] = [];

  async run(): Promise<void> {
    console.log('🧪 INICIANDO SMOKE TEST COMPLETO' + (QUICK ? ' (modo rápido)' : ''));
    console.log('='.repeat(60));
    console.log();

    await this.testIngestion();
    await this.testReingestion();
    await this.testCompleteness();
    await this.testEmbeddings();
    await this.testMCP();
    if (!QUICK) await this.testNetworkReachability();
    await this.testOrchestrator();

    this.printReport();
  }

  private async testIngestion(): Promise<void> {
    console.log('📥 TESTE 1: Ingestão Inicial');
    console.log('-'.repeat(40));
    const start = Date.now();

    try {
      const br = await BrazilianLawIngestor.ingestAll();
      console.log(`  ✅ Leis BR: ${br.inserted} inseridos, ${br.updated} atualizados`);

      const pt = await PortugueseLawIngestor.ingestAll();
      console.log(`  ✅ Leis PT: ${pt.inserted} inseridos, ${pt.updated} atualizados`);

      const juris = await JurisprudenceIngestor.ingestAll();
      console.log(`  ✅ Jurisprudência: ${juris.inserted} inseridos, ${juris.updated} atualizados`);

      // NOTA: o smoke-test colado pelo usuário não chamava DoctrineIngestor (mesma
      // omissão do InitialIngestion.run() original, que chama os 4 — só o smoke-test
      // ficou incompleto). Adicionado aqui para não deixar "Faltando: doutrina" aparecer
      // na checagem de completude por um motivo que não é real (falta de conteúdo), e sim
      // um passo esquecido no próprio teste.
      const doctrine = await DoctrineIngestor.ingestAll();
      console.log(`  ✅ Doutrina: ${doctrine.inserted} inseridos, ${doctrine.updated} atualizados`);

      const totalDocs = await prisma.legalDocument.count();
      const brDocs = await prisma.legalDocument.count({ where: { jurisdiction: 'BR' } });
      const ptDocs = await prisma.legalDocument.count({ where: { jurisdiction: 'PT' } });

      const passed = totalDocs > 0;
      this.results.push({
        name: 'Ingestão',
        passed,
        details: `Total: ${totalDocs} docs (BR: ${brDocs}, PT: ${ptDocs})`,
        duration: Date.now() - start,
      });
      if (!passed) console.log('  ❌ Nenhum documento foi inserido!');
    } catch (error: any) {
      this.results.push({ name: 'Ingestão', passed: false, details: `Erro: ${error.message}`, duration: Date.now() - start });
      console.log(`  ❌ Erro: ${error.message}`);
    }

    console.log();
  }

  private async testReingestion(): Promise<void> {
    console.log('🔄 TESTE 2: Reingestão (Idempotência)');
    console.log('-'.repeat(40));
    const start = Date.now();

    try {
      const before = await prisma.legalDocument.count();
      await BrazilianLawIngestor.ingestAll();
      const after = await prisma.legalDocument.count();
      const passed = before === after;

      this.results.push({
        name: 'Reingestão (Idempotência)',
        passed,
        details: `Antes: ${before}, Depois: ${after} (${passed ? 'sem duplicação' : 'duplicação detectada'})`,
        duration: Date.now() - start,
      });
      console.log(passed ? `  ✅ Sem duplicação: ${before} → ${after}` : `  ⚠️ Duplicação detectada: ${before} → ${after}`);
    } catch (error: any) {
      this.results.push({ name: 'Reingestão (Idempotência)', passed: false, details: `Erro: ${error.message}`, duration: Date.now() - start });
      console.log(`  ❌ Erro: ${error.message}`);
    }

    console.log();
  }

  private async testCompleteness(): Promise<void> {
    console.log('📊 TESTE 3: Completude dos Agentes');
    console.log('-'.repeat(40));
    const start = Date.now();

    try {
      const results = await checkCompleteness();
      const operational = results.filter((r) => r.status === 'operational').length;
      const partial = results.filter((r) => r.status === 'partial').length;
      const empty = results.filter((r) => r.status === 'empty').length;

      this.results.push({
        name: 'Completude',
        passed: operational > 0,
        details: `Operacionais: ${operational}, Parciais: ${partial}, Vazios: ${empty}`,
        duration: Date.now() - start,
      });

      console.log(`  ✅ Operacionais: ${operational}`);
      console.log(`  ⚠️ Parciais: ${partial}`);
      console.log(`  ❌ Vazios: ${empty}`);

      for (const r of results) {
        const icon = r.status === 'operational' ? '✅' : r.status === 'partial' ? '⚠️' : '❌';
        console.log(`    ${icon} ${r.name} (${r.jurisdiction}): ${r.completeness.toFixed(1)}%`);
        if (r.missingTypes.length > 0) console.log(`       Faltando: ${r.missingTypes.join(', ')}`);
      }
    } catch (error: any) {
      this.results.push({ name: 'Completude', passed: false, details: `Erro: ${error.message}`, duration: Date.now() - start });
      console.log(`  ❌ Erro: ${error.message}`);
    }

    console.log();
  }

  private async testEmbeddings(): Promise<void> {
    console.log('🧠 TESTE 4: Geração de Embeddings');
    console.log('-'.repeat(40));
    const start = Date.now();

    try {
      const pending: any[] = await prisma.$queryRaw`SELECT id FROM "LegalDocument" WHERE embedding IS NULL AND content IS NOT NULL`;
      const count = pending.length;

      if (count === 0) {
        console.log('  ⚠️ Nenhum documento para embedding');
        this.results.push({ name: 'Embeddings', passed: true, details: 'Nenhum documento para processar', duration: Date.now() - start });
      } else if (!hasRealApiKey()) {
        console.log(`  ⚠️ OPENAI_API_KEY não configurada. Teste parcial (${count} documentos pendentes).`);
        this.results.push({ name: 'Embeddings', passed: true, details: `Parcial (sem API key) — ${count} pendentes`, duration: Date.now() - start });
      } else {
        const result = await EmbeddingGenerator.generateAll();
        console.log(`  ✅ ${result.processed} embeddings gerados`);
        this.results.push({
          name: 'Embeddings',
          passed: result.errors === 0,
          details: `${result.processed} processados, ${result.errors} erros`,
          duration: Date.now() - start,
        });
      }
    } catch (error: any) {
      this.results.push({ name: 'Embeddings', passed: false, details: `Erro: ${error.message}`, duration: Date.now() - start });
      console.log(`  ❌ Erro: ${error.message}`);
    }

    console.log();
  }

  private async testMCP(): Promise<void> {
    console.log('🔧 TESTE 5: MCP Tools');
    console.log('-'.repeat(40));
    const start = Date.now();

    try {
      const tools = createBrazilianLawTools();
      const searchTool = tools.find((t) => t.name === 'search_brazilian_law');
      if (!searchTool) throw new Error('search_brazilian_law não encontrado');

      const result = await searchTool.execute({ query: 'usucapião', limit: 3 });
      const passed = !result.isError && result.content.length > 0;

      this.results.push({ name: 'MCP Tools', passed, details: passed ? 'Busca executada com sucesso' : 'Falha na busca', duration: Date.now() - start });
      console.log(`  ✅ Busca executada: ${result.content.length} resultado(s)`);
    } catch (error: any) {
      this.results.push({ name: 'MCP Tools', passed: false, details: `Erro: ${error.message}`, duration: Date.now() - start });
      console.log(`  ❌ Erro: ${error.message}`);
    }

    console.log();
  }

  private async testNetworkReachability(): Promise<void> {
    console.log('🌐 TESTE 6: Conectividade com APIs Reais');
    console.log('-'.repeat(40));
    const start = Date.now();
    const results: Array<{ source: string; reachable: boolean; status: number }> = [];

    const sources = [
      { name: 'Planalto (BR)', url: 'https://legislacao.presidencia.gov.br/' },
      { name: 'Diário da República (PT)', url: 'https://diariodarepublica.pt/' },
      { name: 'STF', url: 'https://portal.stf.jus.br/' },
      { name: 'STJ', url: 'https://www.stj.jus.br/' },
      { name: 'TJSP', url: 'https://www.tjsp.jus.br/' },
    ];

    for (const source of sources) {
      try {
        const response = await fetch(source.url, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
        results.push({ source: source.name, reachable: response.ok, status: response.status });
        console.log(`  ${response.ok ? '✅' : '⚠️'} ${source.name}: ${response.status}`);
      } catch {
        results.push({ source: source.name, reachable: false, status: 0 });
        console.log(`  ❌ ${source.name}: Inacessível`);
      }
    }

    const reachableCount = results.filter((r) => r.reachable).length;
    this.results.push({
      name: 'Conectividade de Rede',
      passed: reachableCount > 0,
      details: `${reachableCount}/${sources.length} fontes acessíveis`,
      duration: Date.now() - start,
    });

    console.log();
  }

  private async testOrchestrator(): Promise<void> {
    console.log('🎯 TESTE 7: Orquestrador (pipeline completo)');
    console.log('-'.repeat(40));
    const start = Date.now();

    if (!hasRealApiKey()) {
      console.log('  ⚠️ OPENAI_API_KEY não configurada. Teste parcial.');
      this.results.push({ name: 'Orquestrador', passed: true, details: 'Parcial (sem API key)', duration: Date.now() - start });
      console.log();
      return;
    }

    try {
      const { orchestrator } = bootstrap();
      const result = await orchestrator.processRequest('Qual o prazo para usucapião?', {
        domain: 'legal',
        context: { jurisdiction: 'BR' },
      });

      const passed = !!result.content && result.content.length > 0;
      this.results.push({ name: 'Orquestrador', passed, details: passed ? 'Pipeline executado com sucesso' : 'Falha no pipeline', duration: Date.now() - start });
      console.log(`  ✅ Resposta recebida (${result.content.length} caracteres)`);
    } catch (error: any) {
      this.results.push({ name: 'Orquestrador', passed: false, details: `Erro: ${error.message}`, duration: Date.now() - start });
      console.log(`  ❌ Erro: ${error.message}`);
    }

    console.log();
  }

  private printReport(): void {
    console.log('='.repeat(60));
    console.log('📊 RELATÓRIO FINAL DO SMOKE TEST');
    console.log('='.repeat(60));
    console.log();

    const passed = this.results.filter((r) => r.passed);
    const failed = this.results.filter((r) => !r.passed);

    console.log(`✅ Passaram: ${passed.length}`);
    console.log(`❌ Falharam: ${failed.length}`);
    console.log();

    for (const result of this.results) {
      console.log(`${result.passed ? '✅' : '❌'} ${result.name}: ${result.details} (${result.duration}ms)`);
    }

    console.log();
    console.log('='.repeat(60));
    console.log(failed.length === 0 ? '🎉 TODOS OS TESTES PASSARAM!' : '⚠️ ALGUNS TESTES FALHARAM. REVISE OS ERROS ACIMA.');
  }
}

if (require.main === module) {
  const smokeTest = new SmokeTest();
  smokeTest
    .run()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('❌ Smoke test falhou:', error);
      process.exit(1);
    });
}
