// scripts/schedule/ingestion-schedule.ts
//
// Colado literalmente pelo usuário — nenhuma mudança necessária além dos caminhos
// relativos, que já batem com a estrutura de pastas usada aqui
// (src/ingest/index.ts, src/validate/check-completeness.ts).

import cron from 'node-cron';
import { InitialIngestion } from '../ingest/index';
import { checkCompleteness } from '../validate/check-completeness';

console.log('⏰ Iniciando scheduler de ingestão...');

// Diariamente às 2h da manhã - atualiza jurisprudência
cron.schedule('0 2 * * *', async () => {
  console.log('🔄 Atualizando jurisprudência...');
  try {
    await InitialIngestion.run();
    console.log('✅ Atualização concluída');
  } catch (error) {
    console.error('❌ Erro na atualização:', error);
  }
});

// Aos domingos às 3h - ingestão completa
cron.schedule('0 3 * * 0', async () => {
  console.log('📚 Reingestão completa...');
  try {
    await InitialIngestion.run();
    await checkCompleteness();
    console.log('✅ Reingestão concluída');
  } catch (error) {
    console.error('❌ Erro na reingestão:', error);
  }
});

// A cada 6 horas - verifica qualidade
cron.schedule('0 */6 * * *', async () => {
  console.log('🔍 Verificando qualidade...');
  try {
    const results = await checkCompleteness();
    const operational = results.filter((r) => r.status === 'operational').length;
    console.log(`📊 Agentes operacionais: ${operational}/${results.length}`);
  } catch (error) {
    console.error('❌ Erro na verificação:', error);
  }
});

console.log('✅ Scheduler iniciado!');
console.log('   - Atualização diária às 2h');
console.log('   - Reingestão semanal aos domingos 3h');
console.log('   - Verificação de qualidade a cada 6h');
