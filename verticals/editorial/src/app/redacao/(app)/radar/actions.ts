"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireDesk, requireUser } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { isUuid, str } from "@/lib/forms";
import { dismissItem, promoteToIdea, runRadar } from "@/lib/radar";

function done(kind: "ok" | "erro", msg: string): never {
  redirect(`/redacao/radar?${kind}=${encodeURIComponent(msg)}`);
}

export async function promoteAction(form: FormData) {
  const { ctx } = await requireUser();
  const item = str(form, "item", 40);
  if (!isUuid(item)) done("erro", "Entrada inválida.");
  let storyId = "";
  try {
    storyId = (await promoteToIdea(ctx, item)).story.id;
  } catch (e) {
    done("erro", (e as Error).message);
  }
  revalidatePath("/redacao/radar");
  redirect(`/redacao/pecas/${storyId}?ok=${encodeURIComponent("Ideia criada a partir do radar. Revê o ângulo e propõe-a como pauta.")}`);
}

export async function dismissAction(form: FormData) {
  const { ctx } = await requireUser();
  const item = str(form, "item", 40);
  if (!isUuid(item)) done("erro", "Entrada inválida.");
  try {
    await dismissItem(ctx, item);
  } catch (e) {
    done("erro", (e as Error).message);
  }
  revalidatePath("/redacao/radar");
  done("ok", "Entrada descartada.");
}

export async function addFeedAction(form: FormData) {
  const { ctx } = await requireDesk();
  const name = str(form, "name", 200), url = str(form, "feed_url", 1000);
  if (!name || !url.startsWith("https://")) done("erro", "Indica o nome e um endereço https:// do feed.");
  const tier = str(form, "tier", 20), scope = str(form, "scope", 20);
  try {
    await withCtx(ctx, (tx) => tx`insert into feed_sources (publication_id, name, feed_url, tier, category, scope, interval_minutes)
      values (${ctx.publicationId}, ${name}, ${url}, ${["primary", "institutional", "media"].includes(tier) ? tier : "media"},
        ${str(form, "category", 80)}, ${["local", "national", "international"].includes(scope) ? scope : "local"},
        ${Math.min(10080, Math.max(15, Number(form.get("interval_minutes")) || 60))})`);
  } catch (e) {
    done("erro", (e as { code?: string }).code === "23505" ? "Esse feed já está no radar." : "Não foi possível acrescentar o feed.");
  }
  revalidatePath("/redacao/radar");
  done("ok", "Fonte acrescentada. Só é lida se o domínio estiver na lista autorizada.");
}

export async function toggleFeedAction(form: FormData) {
  const { ctx } = await requireDesk();
  const source = str(form, "source", 40);
  if (!isUuid(source)) done("erro", "Fonte inválida.");
  await withCtx(ctx, (tx) => tx`update feed_sources set active = not active where id = ${source}`);
  revalidatePath("/redacao/radar");
  done("ok", "Estado da fonte alterado.");
}

export async function runNowAction() {
  const { user, ctx } = await requireDesk();
  let msg = "";
  let kind: "ok" | "erro" = "ok";
  try {
    const all = await withCtx(ctx, (tx) => tx<{ id: string }[]>`select id from feed_sources where active`);
    const r = await runRadar(user.publicationId, { sourceIds: all.map((x) => x.id) });
    const inserted = r.sources.reduce((n, s) => n + s.inserted, 0);
    const failed = r.sources.filter((s) => s.status === "error" || s.status === "blocked");
    msg = `Radar lido: ${r.sources.length} fontes, ${inserted} entradas novas.`;
    if (failed.length) {
      kind = failed.length === r.sources.length ? "erro" : "ok";
      msg += ` ${failed.length} fontes falharam (${failed.slice(0, 3).map((s) => `${s.name}: ${s.error ?? s.status}`).join("; ")}).`;
    }
  } catch (e) {
    kind = "erro";
    msg = `O radar falhou: ${(e as Error).message}`;
  }
  revalidatePath("/redacao/radar");
  done(kind, msg);
}
