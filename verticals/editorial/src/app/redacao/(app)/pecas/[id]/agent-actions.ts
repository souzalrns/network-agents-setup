"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireUser } from "@/lib/auth";
import { canWrite } from "@/lib/context";
import { isUuid, str } from "@/lib/forms";
import { runAgentForStory } from "@/lib/agent-bridge";

export async function runAgentAction(form: FormData) {
  const { user, ctx } = await requireUser();
  const story = str(form, "story", 40), agent = str(form, "agent", 20);
  const path = `/redacao/pecas/${story}#agentes`;
  if (!isUuid(story) || !["research", "factcheck", "editor"].includes(agent)) redirect("/redacao/pautas");
  if (!canWrite(user.role)) redirect(`${path.replace("#agentes", "")}?erro=${encodeURIComponent("O teu papel não pede trabalho aos agentes.")}#agentes`);
  const r = await runAgentForStory(ctx, agent as "research" | "factcheck" | "editor", story);
  revalidatePath(`/redacao/pecas/${story}`);
  const kind = r.ok ? "ok" : "erro";
  redirect(`/redacao/pecas/${story}?${kind}=${encodeURIComponent(r.message)}#agentes`);
}
