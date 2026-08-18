// scripts/validate/test-agents.ts
//
// Colado literalmente pelo usuário, com uma única correção obrigatória: o texto original
// tinha `const orchestrator = new Orchestrator(/* ... */);` — um placeholder que não
// compila (o construtor real exige agentFactory, router, planner, executor, memory,
// hitlManager). Trocado por `bootstrap()` (../bootstrap.ts), que monta a mesma cadeia
// real usada em apps/api/src/index.ts.

import { bootstrap } from '../bootstrap';

interface TestCase {
  query: string;
  jurisdiction: 'BR' | 'PT';
  expectedKeywords: string[];
  minLength: number;
}

export async function testAgents(): Promise<void> {
  const { orchestrator } = bootstrap();

  const testCases: TestCase[] = [
    {
      query: 'Qual o prazo para contestar uma ação trabalhista?',
      jurisdiction: 'BR',
      expectedKeywords: ['prazo', 'trabalhista', 'dias'],
      minLength: 50,
    },
    {
      query: 'Quais os requisitos para usucapião no Brasil?',
      jurisdiction: 'BR',
      expectedKeywords: ['usucapião', 'posse', 'anos'],
      minLength: 100,
    },
    {
      query: 'Como funciona a LGPD para pequenas empresas?',
      jurisdiction: 'BR',
      expectedKeywords: ['LGPD', 'dados', 'proteção'],
      minLength: 80,
    },
    {
      query: 'Qual o valor da multa por atraso no FGTS?',
      jurisdiction: 'BR',
      expectedKeywords: ['FGTS', 'multa', 'percentual'],
      minLength: 50,
    },
    {
      query: 'Quais são os direitos do consumidor em compras online?',
      jurisdiction: 'BR',
      expectedKeywords: ['consumidor', 'arrependimento', 'prazo'],
      minLength: 80,
    },
  ];

  console.log('🧪 TESTANDO AGENTES JURÍDICOS');
  console.log('='.repeat(60));

  for (const test of testCases) {
    console.log(`\n📝 Query: ${test.query}`);
    console.log(`   Jurisdição: ${test.jurisdiction}`);

    try {
      const result = await orchestrator.processRequest(test.query, {
        domain: 'legal',
        context: { jurisdiction: test.jurisdiction },
      });

      const content = result.content || '';

      // Verifica tamanho
      const hasMinLength = content.length >= test.minLength;

      // Verifica palavras-chave
      const foundKeywords = test.expectedKeywords.filter((kw) =>
        content.toLowerCase().includes(kw.toLowerCase())
      );

      console.log(`   ✅ Resposta: ${content.slice(0, 200)}...`);
      console.log(`   📊 Tamanho: ${content.length} caracteres (${hasMinLength ? '✅' : '⚠️'})`);
      console.log(`   📊 Keywords encontradas: ${foundKeywords.length}/${test.expectedKeywords.length}`);
      console.log(`   📊 Status: ${hasMinLength && foundKeywords.length > 0 ? '✅ APROVADO' : '⚠️ REVISAR'}`);
    } catch (error) {
      console.error(`   ❌ Erro: ${error}`);
    }
  }

  console.log('\n✅ Testes concluídos!');
}

if (require.main === module) {
  testAgents();
}
