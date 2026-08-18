import { PrismaClient } from '@prisma/client';

// Instância compartilhada pelas ferramentas MCP de Direito BR/PT.
export const prisma = new PrismaClient();
