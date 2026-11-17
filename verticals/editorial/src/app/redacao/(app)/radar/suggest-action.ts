"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { runRadarSuggestions } from "@/lib/agent-bridge";
import { requireUser } from "@/lib/auth";

export async function suggestAction() {
  const { ctx } = await requireUser();
  const r = await runRadarSuggestions(ctx);
  revalidatePath("/redacao/radar");
  redirect(`/redacao/radar?${r.ok ? "ok" : "erro"}=${encodeURIComponent(r.message)}#propostas`);
}
