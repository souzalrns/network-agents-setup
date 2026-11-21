import type { Ctx } from "./context";
import { db, withCtx } from "./db";
import { EditorialError } from "./stories";

/**
 * Newsletter: a lista é desta base, com o consentimento registado (o texto aceite e a data) e anulação por link.
 * O envio fica para um serviço de email quando houver; a exportação leva o link de anulação de cada pessoa.
 */
export const CONSENT_TEXT = (pubName: string) =>
  `Aceito receber a newsletter de ${pubName} por email. Posso anular a inscrição a qualquer momento pelo link em cada envio. Os dados são tratados segundo a política de privacidade.`;

export async function subscribe(publicationId: string, email: string, consent: string): Promise<void> {
  const e = email.trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e) || e.length > 254) throw new EditorialError("Indica um email válido.");
  if (!consent.trim()) throw new EditorialError("É preciso aceitar para te inscreveres.");
  await db()`select editorial.public_subscribe(${publicationId}, ${e}, ${consent})`;
}

export async function unsubscribe(token: string): Promise<boolean> {
  if (!/^[0-9a-f]{36}$/.test(token)) return false;
  const [r] = await db()<{ ok: boolean }[]>`select editorial.public_unsubscribe(${token}) as ok`;
  return r?.ok === true;
}

export interface SubscriberRow { email: string; status: string; consent_at: Date; unsubscribed_at: Date | null; unsubscribe_token: string }

export async function listSubscribers(ctx: Ctx): Promise<SubscriberRow[]> {
  return withCtx(ctx, (tx) => tx<SubscriberRow[]>`select email::text as email, status, consent_at, unsubscribed_at, unsubscribe_token
    from subscribers order by consent_at desc`);
}

const csvCell = (v: string) => (/[",\n;]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);

/** CSV para importar num serviço de envio: só as inscrições activas, com o link de anulação de cada uma. */
export function subscribersCsv(rows: SubscriberRow[], baseUrl: string): string {
  const base = baseUrl.replace(/\/+$/, "");
  const lines = [["email", "inscrito_em", "link_anular"].join(",")];
  for (const r of rows.filter((x) => x.status === "active")) {
    lines.push([r.email, new Date(r.consent_at).toISOString(), `${base}/newsletter/anular?t=${r.unsubscribe_token}`].map(csvCell).join(","));
  }
  return lines.join("\n") + "\n";
}
