import postgres from "postgres";
// @ts-expect-error módulo JavaScript partilhado com db/provision.mjs, sem tipos
import { appDatabaseUrl } from "../../db/app-url.mjs";
import type { Ctx } from "./context";

/**
 * Ligação da APLICAÇÃO: o papel `editorial_app`, sem privilégios de dono. Sozinha não vê nenhuma linha:
 * cada operação corre numa transacção que declara a publicação e quem actua (`withCtx`), e é o Postgres
 * (RLS e triggers) que impõe o isolamento e as regras de aprovação.
 */
export type Sql = postgres.Sql;
export type Tx = postgres.TransactionSql;

let client: Sql | undefined;

export function db(): Sql {
  if (!client) {
    // EDITORIAL_DATABASE_URL, ou derivada da ligação do dono criada pela integração Neon (db/app-url.mjs)
    const url = appDatabaseUrl();
    if (!url) throw new Error("Falta EDITORIAL_DATABASE_URL (ligação do papel editorial_app).");
    client = postgres(url, {
      max: Number(process.env.EDITORIAL_DB_POOL ?? 5),
      prepare: false, // compatível com poolers em modo transacção
      onnotice: () => {},
      transform: { undefined: null },
    });
  }
  return client;
}

export async function closeDb(): Promise<void> {
  if (client) {
    await client.end({ timeout: 5 });
    client = undefined;
  }
}

/** Corre `fn` numa transacção com o contexto do actor. O contexto morre com a transacção. */
export async function withCtx<T>(ctx: Ctx, fn: (tx: Tx) => Promise<T>, note = ""): Promise<T> {
  return db().begin(async (tx) => {
    // search_path dentro da transacção: os poolers (PgBouncer, Neon) ignoram o parâmetro enviado ao ligar
    await tx`select
      set_config('search_path', 'editorial, public', true),
      set_config('app.publication_id', ${ctx.publicationId}, true),
      set_config('app.actor_kind', ${ctx.kind}, true),
      set_config('app.user_id', ${ctx.userId ?? ""}, true),
      set_config('app.role', ${ctx.role ?? ""}, true),
      set_config('app.actor_label', ${ctx.label ?? ""}, true),
      set_config('app.note', ${note}, true)`;
    return fn(tx);
  }) as Promise<T>;
}

/** Mensagem legível de um erro levantado por uma regra da base de dados. */
export function dbMessage(e: unknown): string | null {
  const err = e as { code?: string; message?: string };
  if (err?.code === "P0001" && err.message) return err.message; // raise exception dos triggers
  if (err?.code === "42501") return "Não tens permissão para fazer isto.";
  if (err?.code === "23505") return "Já existe um registo igual.";
  return null;
}
