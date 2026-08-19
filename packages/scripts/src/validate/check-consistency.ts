// scripts/validate/check-consistency.ts
//
// Verifica consistência entre o que está documentado (docs/STATUS.md),
// a config de agentes (config/agents.config.ts) e o conteúdo real de
// ingestão (seeds BR/PT/jurisprudência/doutrina).
//
// Objetivo: qualquer sessão futura (humana ou IA) consegue detetar
// divergência entre "o que o STATUS diz" e "o que o código realmente tem"
// sem reler o histórico de conversas.
//
// Não depende de Postgres nem de Supabase — corre só sobre ficheiros do
// repo. Para completude de agentes contra banco, usar validate:completeness.

import fs from 'fs';
import path from 'path';

interface CheckResult {
  id: string;
  ok: boolean;
  level: 'error' | 'warning' | 'info';
  message: string;
}

const ROOT = path.resolve(__dirname, '../../../..');

function read(rel: string): string {
  return fs.readFileSync(path.join(ROOT, rel), 'utf8');
}

function exists(rel: string): boolean {
  return fs.existsSync(path.join(ROOT, rel));
}

function countMatches(text: string, pattern: RegExp): number {
  const m = text.match(pattern);
  return m ? m.length : 0;
}

/** Extrai o número de entradas da lista de leis a partir do getLawList() */
function countLawListEntries(source: string): number {
  // Conta objetos `{ type: ...` dentro de getLawList (aprox. fiável no formato atual)
  const listBlock = source.match(/getLawList\(\)[\s\S]*?return\s*\[([\s\S]*?)\];/);
  if (!listBlock) return 0;
  return countMatches(listBlock[1], /\{\s*type:/g);
}

/** Extrai chaves do mapa de seed content (ex.: '10406/2002') */
function countSeedEntries(source: string, mapName: string): number {
  // BUG CORRIGIDO 18/08/2026: template literal comum (backtick) processa escapes de
  // string ANTES de virar regex — `\s`/`\S` não são sequências de escape reconhecidas em
  // strings JS, então o backslash é descartado silenciosamente (`\s` vira só `s`),
  // corrompendo o padrão para `[sS]` em vez de "qualquer caractere". Resultado: o regex
  // nunca casava e countSeedEntries() sempre retornava 0, mesmo com os verbetes presentes
  // (confirmado rodando manualmente contra brazilian-law.ts real: 15 entradas existem,
  // mas o check reportava 0). `String.raw` preserva os backslashes literalmente, sem
  // processar como escape de string — é o jeito certo de montar regex dinâmico assim.
  const re = new RegExp(String.raw`const ${mapName}[\s\S]*?=\s*\{([\s\S]*?)\n\};`);
  const block = source.match(re);
  if (!block) return 0;
  return countMatches(block[1], /['"]\d+\/\d+['"]\s*:/g);
}

function checkStatusDoc(): CheckResult[] {
  const results: CheckResult[] = [];
  const rel = 'docs/STATUS.md';

  if (!exists(rel)) {
    results.push({
      id: 'status.exists',
      ok: false,
      level: 'error',
      message: 'docs/STATUS.md não existe — índice deste repo em falta',
    });
    return results;
  }

  const status = read(rel);
  results.push({
    id: 'status.exists',
    ok: true,
    level: 'info',
    message: 'docs/STATUS.md presente',
  });

  const requiredPhrases: Array<{ id: string; phrase: string; why: string }> = [
    {
      id: 'status.two-layers',
      phrase: 'duas camadas',
      why: 'princípio de arquitetura (pública/genérica vs privada/produção)',
    },
    {
      id: 'status.agent-network-mcp',
      phrase: 'agent-network-mcp',
      why: 'referência à camada privada de produção',
    },
    {
      id: 'status.content-real',
      phrase: 'Conteúdo real curado',
      why: 'marca que o pipeline jurídico já não é placeholder',
    },
    {
      id: 'status.isolation',
      phrase: 'isolamento',
      why: 'pendência de isolamento de banco ainda documentada',
    },
  ];

  for (const r of requiredPhrases) {
    const ok = status.includes(r.phrase);
    results.push({
      id: r.id,
      ok,
      level: ok ? 'info' : 'error',
      message: ok
        ? `STATUS menciona "${r.phrase}" (${r.why})`
        : `STATUS NÃO menciona "${r.phrase}" — esperado para ${r.why}`,
    });
  }

  // Placeholder residual no STATUS seria um sinal de desatualização
  if (/Conteúdo simulado para teste/i.test(status)) {
    results.push({
      id: 'status.no-placeholder-claim',
      ok: false,
      level: 'error',
      message: 'STATUS ainda menciona "Conteúdo simulado para teste" — desatualizado',
    });
  } else {
    results.push({
      id: 'status.no-placeholder-claim',
      ok: true,
      level: 'info',
      message: 'STATUS não reivindica mais conteúdo simulado',
    });
  }

  return results;
}

function checkNoPlaceholderInSeeds(): CheckResult[] {
  const results: CheckResult[] = [];
  const files = [
    'packages/scripts/src/ingest/brazilian-law.ts',
    'packages/scripts/src/ingest/portuguese-law.ts',
    'packages/scripts/src/ingest/jurisprudence.ts',
    'packages/scripts/src/ingest/doctrine.ts',
  ];

  const banned = [
    /Conteúdo simulado para teste/i,
    /placeholder óbvio/i,
    /RE-\d{6}-\d/, // números de processo fabricados do estilo antigo
  ];

  for (const rel of files) {
    if (!exists(rel)) {
      results.push({
        id: `seed.exists.${path.basename(rel)}`,
        ok: false,
        level: 'error',
        message: `Ficheiro de ingestão em falta: ${rel}`,
      });
      continue;
    }

    const src = read(rel);
    let clean = true;
    for (const pattern of banned) {
      if (pattern.test(src)) {
        // Permitir menção em comentários históricos ("substituiu placeholder")
        // mas falhar se aparecer em strings de conteúdo ativo
        const lines = src.split('\n');
        const offenders = lines.filter(
          (l) => pattern.test(l) && !l.trim().startsWith('//') && !l.trim().startsWith('*')
        );
        if (offenders.length > 0) {
          clean = false;
          results.push({
            id: `seed.placeholder.${path.basename(rel)}`,
            ok: false,
            level: 'error',
            message: `${rel} ainda contém placeholder ativo: ${pattern}`,
          });
        }
      }
    }
    if (clean) {
      results.push({
        id: `seed.clean.${path.basename(rel)}`,
        ok: true,
        level: 'info',
        message: `${path.basename(rel)} sem placeholder ativo`,
      });
    }
  }

  return results;
}

function checkLawCounts(): CheckResult[] {
  const results: CheckResult[] = [];

  // STATUS diz: 15 leis BR, 9 leis PT
  const EXPECTED_BR = 15;
  const EXPECTED_PT = 9;

  if (!exists('packages/scripts/src/ingest/brazilian-law.ts')) {
    results.push({
      id: 'laws.br.exists',
      ok: false,
      level: 'error',
      message: 'brazilian-law.ts em falta',
    });
  } else {
    const br = read('packages/scripts/src/ingest/brazilian-law.ts');
    const listCount = countLawListEntries(br);
    const seedCount = countSeedEntries(br, 'BR_LAW_CONTENT');

    results.push({
      id: 'laws.br.list',
      ok: listCount === EXPECTED_BR,
      level: listCount === EXPECTED_BR ? 'info' : 'error',
      message:
        listCount === EXPECTED_BR
          ? `BR getLawList(): ${listCount} entradas (esperado ${EXPECTED_BR})`
          : `BR getLawList(): ${listCount} entradas — STATUS espera ${EXPECTED_BR}`,
    });

    results.push({
      id: 'laws.br.seed',
      ok: seedCount === EXPECTED_BR,
      level: seedCount === EXPECTED_BR ? 'info' : 'warning',
      message:
        seedCount === EXPECTED_BR
          ? `BR_LAW_CONTENT: ${seedCount} verbetes curados`
          : `BR_LAW_CONTENT: ${seedCount} verbetes — lista tem ${listCount} (seeds incompletos?)`,
    });
  }

  if (!exists('packages/scripts/src/ingest/portuguese-law.ts')) {
    results.push({
      id: 'laws.pt.exists',
      ok: false,
      level: 'error',
      message: 'portuguese-law.ts em falta',
    });
  } else {
    const pt = read('packages/scripts/src/ingest/portuguese-law.ts');
    const listCount = countLawListEntries(pt);
    const seedCount = countSeedEntries(pt, 'PT_LAW_CONTENT');

    results.push({
      id: 'laws.pt.list',
      ok: listCount === EXPECTED_PT,
      level: listCount === EXPECTED_PT ? 'info' : 'error',
      message:
        listCount === EXPECTED_PT
          ? `PT getLawList(): ${listCount} entradas (esperado ${EXPECTED_PT})`
          : `PT getLawList(): ${listCount} entradas — STATUS espera ${EXPECTED_PT}`,
    });

    results.push({
      id: 'laws.pt.seed',
      ok: seedCount === EXPECTED_PT,
      level: seedCount === EXPECTED_PT ? 'info' : 'warning',
      message:
        seedCount === EXPECTED_PT
          ? `PT_LAW_CONTENT: ${seedCount} verbetes curados`
          : `PT_LAW_CONTENT: ${seedCount} verbetes — lista tem ${listCount}`,
    });
  }

  return results;
}

function checkAgentsConfig(): CheckResult[] {
  const results: CheckResult[] = [];
  const rel = 'config/agents.config.ts';

  if (!exists(rel)) {
    results.push({
      id: 'agents.config.exists',
      ok: false,
      level: 'error',
      message: 'config/agents.config.ts em falta',
    });
    return results;
  }

  const cfg = read(rel);

  // Agentes jurídicos esperados (alinhados com legal-agents.ts e STATUS)
  const expectedLegal = [
    { id: 'legal-orchestrator', layer: 'vertical', visibility: 'private' },
    { id: 'civil-law-br', layer: 'vertical', visibility: 'private' },
    { id: 'civil-law-pt', layer: 'vertical', visibility: 'private' },
    { id: 'legal-research', layer: 'horizontal', visibility: 'public' },
  ];

  for (const agent of expectedLegal) {
    const hasId = cfg.includes(`id: '${agent.id}'`) || cfg.includes(`id: "${agent.id}"`);
    if (!hasId) {
      results.push({
        id: `agents.${agent.id}.exists`,
        ok: false,
        level: 'error',
        message: `Agente '${agent.id}' não encontrado em agents.config.ts`,
      });
      continue;
    }

    // Extrai o bloco do agente (aproximação: do id até o próximo id ou fecho).
    // Mesmo bug de countSeedEntries() acima — String.raw para não perder os `\s`.
    const blockRe = new RegExp(
      String.raw`id:\s*['"]${agent.id}['"][\s\S]*?(?=id:\s*['"]|\];)`,
      'm'
    );
    const block = cfg.match(blockRe)?.[0] || '';

    const hasLayer = block.includes(`layer: '${agent.layer}'`) || block.includes(`layer: "${agent.layer}"`);
    const hasVis =
      block.includes(`visibility: '${agent.visibility}'`) ||
      block.includes(`visibility: "${agent.visibility}"`);

    results.push({
      id: `agents.${agent.id}.layer`,
      ok: hasLayer,
      level: hasLayer ? 'info' : 'error',
      message: hasLayer
        ? `${agent.id}: layer='${agent.layer}' OK`
        : `${agent.id}: layer deveria ser '${agent.layer}'`,
    });

    results.push({
      id: `agents.${agent.id}.visibility`,
      ok: hasVis,
      level: hasVis ? 'info' : 'error',
      message: hasVis
        ? `${agent.id}: visibility='${agent.visibility}' OK`
        : `${agent.id}: visibility deveria ser '${agent.visibility}' (regra public/private)`,
    });
  }

  // methodology-legal deve ser horizontal/public (transversal)
  if (cfg.includes("'methodology-legal'") || cfg.includes('"methodology-legal"')) {
    const blockRe = /id:\s*['"]methodology-legal['"][\s\S]*?(?=id:\s*['"]|\];)/m;
    const block = cfg.match(blockRe)?.[0] || '';
    const ok =
      (block.includes("layer: 'horizontal'") || block.includes('layer: "horizontal"')) &&
      (block.includes("visibility: 'public'") || block.includes('visibility: "public"'));
    results.push({
      id: 'agents.methodology-legal.transversal',
      ok,
      level: ok ? 'info' : 'warning',
      message: ok
        ? 'methodology-legal é horizontal/public (transversal) — correto'
        : 'methodology-legal deveria ser horizontal/public',
    });
  }

  return results;
}

function checkArchitectureMarkers(): CheckResult[] {
  const results: CheckResult[] = [];

  const markers: Array<{ rel: string; id: string }> = [
    { rel: 'docs/estrutura-geral-agentes.md', id: 'arch.estrutura' },
    { rel: 'packages/core/src/orchestrator/Orchestrator.ts', id: 'arch.orchestrator' },
    { rel: 'packages/memory/prisma/schema.prisma', id: 'arch.prisma' },
    { rel: 'docker-compose.yml', id: 'arch.docker-compose' },
  ];

  for (const m of markers) {
    const ok = exists(m.rel);
    results.push({
      id: m.id,
      ok,
      level: ok ? 'info' : 'warning',
      message: ok ? `${m.rel} presente` : `${m.rel} em falta`,
    });
  }

  // docker-compose existe = caminho para isolamento local (item 2 da pendência)
  if (exists('docker-compose.yml')) {
    const dc = read('docker-compose.yml');
    const hasPostgres = /postgres/i.test(dc);
    results.push({
      id: 'arch.docker-postgres',
      ok: hasPostgres,
      level: hasPostgres ? 'info' : 'warning',
      message: hasPostgres
        ? 'docker-compose inclui Postgres (base para isolamento local de demo)'
        : 'docker-compose sem Postgres — isolamento local fica mais difícil',
    });
  }

  return results;
}

export function checkConsistency(): CheckResult[] {
  return [
    ...checkStatusDoc(),
    ...checkNoPlaceholderInSeeds(),
    ...checkLawCounts(),
    ...checkAgentsConfig(),
    ...checkArchitectureMarkers(),
  ];
}

function printReport(results: CheckResult[]): number {
  const errors = results.filter((r) => !r.ok && r.level === 'error');
  const warnings = results.filter((r) => !r.ok && r.level === 'warning');
  const infos = results.filter((r) => r.ok);

  console.log('\n🔍 VERIFICAÇÃO DE CONSISTÊNCIA (STATUS ↔ código ↔ agentes)');
  console.log('='.repeat(64));
  console.log(`Total checks: ${results.length}`);
  console.log(`✅ OK: ${infos.length}`);
  console.log(`⚠️  Avisos: ${warnings.length}`);
  console.log(`❌ Erros: ${errors.length}`);
  console.log('');

  for (const r of results) {
    const icon = r.ok ? '✅' : r.level === 'error' ? '❌' : '⚠️';
    console.log(`  ${icon} [${r.id}] ${r.message}`);
  }

  console.log('\n' + '='.repeat(64));
  if (errors.length === 0 && warnings.length === 0) {
    console.log('✅ Consistência OK — STATUS, seeds e agents.config alinhados.');
  } else if (errors.length === 0) {
    console.log('⚠️  Sem erros, mas há avisos a rever.');
  } else {
    console.log('❌ Inconsistências detetadas — corrigir antes de publicar o PCU.');
  }

  return errors.length;
}

if (require.main === module) {
  const results = checkConsistency();
  const errorCount = printReport(results);
  process.exit(errorCount > 0 ? 1 : 0);
}
