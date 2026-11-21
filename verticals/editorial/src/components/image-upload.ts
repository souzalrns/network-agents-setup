"use client";
/**
 * Reduz a imagem no browser antes de enviar (máx. 2000 px no lado maior, JPEG ou WebP de qualidade 0,82) e
 * carrega-a para a biblioteca. Uma fotografia de telemóvel de 5 MB fica, em regra, abaixo de 600 KB.
 */
export async function uploadImage(file: File, meta: { alt?: string; credit?: string } = {}): Promise<{ id: string; url: string }> {
  if (!/^image\/(jpeg|png|webp)$/.test(file.type)) throw new Error("Só imagens JPEG, PNG ou WebP.");
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 2000 / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale), h = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w; canvas.height = h;
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, w, h);
  const type = file.type === "image/png" && scale === 1 && file.size < 1_500_000 ? "image/png" : "image/jpeg";
  const blob: Blob = type === "image/png" ? file : await new Promise((ok, ko) => canvas.toBlob((b) => (b ? ok(b) : ko(new Error("Não foi possível converter a imagem."))), type, 0.82));
  const form = new FormData();
  form.set("file", new File([blob], file.name.replace(/\.\w+$/, type === "image/png" ? ".png" : ".jpg"), { type }));
  form.set("width", String(w)); form.set("height", String(h));
  form.set("alt", meta.alt ?? ""); form.set("credit", meta.credit ?? "");
  const r = await fetch("/redacao/media/carregar", { method: "POST", body: form });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error ?? "Não foi possível carregar a imagem.");
  return j;
}
