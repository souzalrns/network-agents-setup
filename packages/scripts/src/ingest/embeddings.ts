// scripts/ingest/embeddings.ts
//
// Colado literalmente pelo usuário, com uma correção estrutural obrigatória:
// `prisma.legalDocument.findMany({ where: { embedding: null, ... } })` não compila e não
// funcionaria mesmo com o client gerado — campos `Unsupported("vector")` são omitidos
// pelo Prisma Client de `where`/`select`/tipos de saída (é uma limitação de fato do
// Prisma para tipos não suportados, não algo específico deste ambiente). Trocado por uma
// query SQL crua equivalente (`prisma.$queryRaw`), que é a forma suportada de ler/filtrar
// uma coluna Unsupported. `saveEmbedding()` já usava `$executeRaw` no original — mantido
// como estava, incluindo o nome de tabela `"LegalDocument"` (correto porque o model não
// tem `@@map`, então o Prisma usa o nome do model como nome da tabela).
//
// Segunda correção, encontrada rodando o smoke-test de verdade (sem OPENAI_API_KEY): o
// texto original fazia `const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })`
// no escopo do módulo — o SDK da OpenAI valida a apiKey e LANÇA no construtor se ela
// estiver ausente. Como `scripts/ingest/index.ts` importa este arquivo incondicionalmente
// (mesmo para quem só quer ingerir leis/jurisprudência, sem gerar embedding nenhum), isso
// derrubava o processo inteiro só de importar o módulo, antes mesmo de rodar qualquer
// ingestão. Trocado por uma instância lazy, criada só quando `generateEmbedding()` é
// chamado de verdade.

import { OpenAI } from 'openai';
import { prisma } from '../db';

let openai: OpenAI | null = null;
function getOpenAIClient(): OpenAI {
  if (!openai) {
    openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  }
  return openai;
}

interface PendingDocument {
  id: string;
  content: string | null;
  summary: string | null;
  title: string;
}

export class EmbeddingGenerator {
  static async generateAll(): Promise<{ processed: number; errors: number }> {
    let processed = 0;
    let errors = 0;

    // Checagem antecipada: sem isso, cada documento pendente entraria no loop abaixo,
    // chamaria getOpenAIClient() e falharia individualmente (1 erro por documento) — só
    // para reportar N vezes o mesmo problema de configuração. Uma única mensagem clara e
    // retorno antecipado é mais honesto do que "N erros" quando a causa é sempre a mesma.
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey || apiKey === 'your-openai-api-key-here') {
      console.log('⚠️ OPENAI_API_KEY não configurada. Pulando geração de embeddings.');
      return { processed: 0, errors: 0 };
    }

    // Busca documentos sem embedding (ver nota de fidelidade no topo do arquivo sobre
    // por que isso precisa ser SQL cru em vez de `prisma.legalDocument.findMany`).
    const documents = await prisma.$queryRaw<PendingDocument[]>`
      SELECT id, content, summary, title
      FROM "LegalDocument"
      WHERE embedding IS NULL AND content IS NOT NULL
      LIMIT 100
    `;

    for (const doc of documents) {
      try {
        const embedding = await this.generateEmbedding(doc.content || doc.summary || doc.title);
        await this.saveEmbedding(doc.id, embedding);
        processed++;
        console.log(`✅ Embedding gerado para ${doc.id}`);
      } catch (error) {
        errors++;
        console.error(`❌ Erro ao gerar embedding para ${doc.id}:`, error);
      }
    }

    return { processed, errors };
  }

  private static async generateEmbedding(text: string): Promise<number[]> {
    const response = await getOpenAIClient().embeddings.create({
      model: 'text-embedding-3-small',
      input: text.slice(0, 8000),
    });

    return response.data[0].embedding;
  }

  private static async saveEmbedding(docId: string, embedding: number[]): Promise<void> {
    // Salva usando pgvector
    await prisma.$executeRaw`
      UPDATE "LegalDocument"
      SET embedding = ${embedding}::vector
      WHERE id = ${docId}
    `;
  }
}

// Executa se for chamado diretamente
if (require.main === module) {
  EmbeddingGenerator.generateAll()
    .then((stats) => {
      console.log('📊 Embeddings:', stats);
      process.exit(0);
    })
    .catch((error) => {
      console.error('❌ Erro:', error);
      process.exit(1);
    });
}
