#!/usr/bin/env node
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
console.log('🔍 Verificando integridade do projeto...\n');
const errors: string[] = [];
const warnings: string[] = [];
// 1. Verifica arquivos necessários
const requiredFiles = [
  'packages/core/src/index.ts',
  'packages/core/src/orchestrator/Orchestrator.ts',
  'packages/core/src/governance/ArchitectureCouncil.ts',
  'packages/core/src/governance/DeliberationEngine.ts',
  'packages/core/src/governance/TrustManager.ts',
  'packages/core/src/governance/CompletenessValidator.ts',
  'packages/core/src/economy/TokenEconomy.ts',
  'packages/core/src/security/SecurityManager.ts',
  'packages/core/src/observability/SelfAwareness.ts',
  'packages/core/src/opportunity/OpportunityRadar.ts',
  'packages/core/src/simulation/OrganizationalSimulator.ts',
  'packages/core/src/immunity/ImmunologicalMemory.ts',
  'packages/memory/prisma/schema.prisma',
  'apps/api/src/index.ts',
  'config/agents.config.ts',
  '.env.example',
];
for (const file of requiredFiles) {
  if (!fs.existsSync(file)) {
    errors.push(`❌ Arquivo não encontrado: ${file}`);
  } else {
    console.log(`✅ ${file}`);
  }
}
// 2. Verifica dependências
try {
  execSync('pnpm list --depth=0', { stdio: 'pipe' });
  console.log('✅ Dependências instaladas');
} catch {
  warnings.push('⚠️ Dependências não instaladas. Execute: pnpm install');
}
// 3. Verifica Prisma
if (fs.existsSync('packages/memory/prisma/schema.prisma')) {
  try {
    execSync('pnpm prisma generate', { cwd: 'packages/memory', stdio: 'pipe' });
    console.log('✅ Prisma client gerado');
  } catch {
    warnings.push('⚠️ Prisma client não gerado. Execute: cd packages/memory && pnpm prisma generate');
  }
} else {
  errors.push('❌ Schema Prisma não encontrado');
}
// 4. Verifica variáveis de ambiente
if (!fs.existsSync('.env')) {
  warnings.push('⚠️ Arquivo .env não encontrado. Copie .env.example para .env');
}
// 5. Sumário
console.log('\n' + '='.repeat(50));
console.log('📊 RESUMO DA VERIFICAÇÃO');
console.log('='.repeat(50));
if (errors.length === 0 && warnings.length === 0) {
  console.log('✅ Projeto 100% íntegro!');
} else {
  if (errors.length > 0) {
    console.log('\n❌ ERROS:');
    for (const err of errors) {
      console.log(`  ${err}`);
    }
  }
  if (warnings.length > 0) {
    console.log('\n⚠️ AVISOS:');
    for (const warn of warnings) {
      console.log(`  ${warn}`);
    }
  }
}
console.log(`\nTotal: ${errors.length} erros, ${warnings.length} avisos`);
process.exit(errors.length > 0 ? 1 : 0);
