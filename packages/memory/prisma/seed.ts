import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();
async function main() {
  console.log('🌱 Seeding database...');
  // Criar usuário admin
  const admin = await prisma.user.upsert({
    where: { email: 'admin@network-agents.local' },
    update: {},
    create: {
      email: 'admin@network-agents.local',
      name: 'Admin',
      preferences: { theme: 'dark', language: 'pt' },
    },
  });
  console.log('✅ Admin user created:', admin.email);
  // Criar conversa inicial
  const conversation = await prisma.conversation.create({
    data: {
      userId: admin.id,
      title: 'Bem-vindo ao Network Agents',
    },
  });
  console.log('✅ Initial conversation created:', conversation.id);
  console.log('🌱 Seeding complete!');
}
main()
  .catch((e) => {
    console.error('❌ Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
