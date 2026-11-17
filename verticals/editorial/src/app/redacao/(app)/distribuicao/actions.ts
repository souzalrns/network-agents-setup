"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireDesk } from "@/lib/auth";
import { dispatchApproved } from "@/lib/postiz";

export async function dispatchAction() {
  const { ctx } = await requireDesk();
  let msg: string;
  let kind = "ok";
  try {
    const r = await dispatchApproved(ctx);
    const count = (s: string) => r.filter((x) => x.status === s).length;
    msg = `Enviados ${count("enviado")}, simulados ${count("simulado")}, já enviados ${count("ja_enviado")}, recusados ${count("recusado")}, com erro ${count("erro")}.`;
    const reasons = [...new Set(r.filter((x) => x.reason).map((x) => x.reason))];
    if (reasons.length) msg += ` Motivos: ${reasons.join("; ")}.`;
    if (count("erro")) kind = "erro";
  } catch (e) {
    kind = "erro"; msg = (e as Error).message;
  }
  revalidatePath("/redacao/distribuicao");
  redirect(`/redacao/distribuicao?${kind}=${encodeURIComponent(msg)}`);
}
