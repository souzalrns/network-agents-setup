import { PrismaClient } from '@prisma/client';

// Cliente Prisma compartilhado por todos os scripts de ingestão/validação/monitoramento.
// Os scripts vivem fora do Orchestrator (MemoryManager mantém seu próprio PrismaClient
// privado, sem expô-lo), então instanciam o deles próprio aqui — mesmo padrão usado por
// MemoryManager.ts (`new PrismaClient()`).
export const prisma = new PrismaClient();
