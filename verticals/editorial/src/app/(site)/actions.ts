"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { subscribe } from "@/lib/newsletter";
import { publicContext } from "@/lib/publication";
import { EditorialError } from "@/lib/stories";

/** Inscrição na newsletter a partir do site. O consentimento guardado é o texto exacto mostrado ao leitor. */
export async function subscribeAction(form: FormData) {
  // campo-armadilha para robôs: uma pessoa nunca o preenche (está escondido)
  if (String(form.get("website") ?? "")) redirect("/newsletter?estado=ok");
  const h = await headers();
  const ctx = await publicContext(h.get("x-forwarded-host") ?? h.get("host"));
  if (!ctx) redirect("/");
  if (form.get("consent") !== "1") redirect("/newsletter?estado=consent");
  try {
    await subscribe(ctx.publicationId, String(form.get("email") ?? ""), String(form.get("consent_text") ?? ""));
  } catch (e) {
    if (e instanceof EditorialError) redirect("/newsletter?estado=email");
    throw e;
  }
  redirect("/newsletter?estado=ok");
}
