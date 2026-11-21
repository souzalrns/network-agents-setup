// Recuperar a palavra-passe sem email, biblioteca de média, newsletter com consentimento e cópia de segurança.
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createResetLink, resetPassword } from "@/lib/accounts";
import { login } from "@/lib/auth-core";
import { exportPublication } from "@/lib/backup";
import { publicCtx } from "@/lib/context";
import { closeDb, withCtx } from "@/lib/db";
import { listMedia, readMedia, saveMedia, sniffImage } from "@/lib/media";
import { listSubscribers, subscribe, subscribersCsv, unsubscribe } from "@/lib/newsletter";
import { closeOwner, type Newsroom, newsroom, ownerDb, PASSWORD } from "./helpers/fixture";

let N: Newsroom;
let O: Newsroom; // outra publicação: nada passa de uma para a outra
beforeAll(async () => { N = await newsroom(); O = await newsroom(); });
afterAll(async () => { await closeDb(); await closeOwner(); });

// PNG de 1x1 válido
const PNG = Uint8Array.from(Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==", "base64"));

describe("recuperar a palavra-passe sem email", () => {
  it("a direção gera um link de uso único; a pessoa troca a palavra-passe e as sessões antigas caem", async () => {
    const { link, expires } = await createResetLink(N.as("director"), N.users.journalist!.id, "https://exemplo.invalid");
    expect(link).toMatch(/^https:\/\/exemplo\.invalid\/redacao\/recuperar\/[A-Za-z0-9_-]{40,}$/);
    expect(expires.getTime() - Date.now()).toBeGreaterThan(23 * 3_600_000);
    const token = link.split("/").pop()!;
    expect(await resetPassword(token, "nova-palavra-passe-123")).toBe(true);
    expect(await resetPassword(token, "outra-tentativa-123")).toBe(false); // uso único
    expect((await login(N.users.journalist!.email, PASSWORD)).ok).toBe(false);
    expect((await login(N.users.journalist!.email, "nova-palavra-passe-123")).ok).toBe(true);
  });

  it("só a direção gera links, não para si própria, nem para um administrador se não for administradora", async () => {
    await expect(createResetLink(N.as("editor"), N.users.journalist!.id, "https://x.invalid")).rejects.toThrow(/só a direcção/);
    await expect(createResetLink(N.as("director"), N.users.director!.id, "https://x.invalid")).rejects.toThrow(/página Conta/);
    await expect(createResetLink(N.as("director"), N.users.admin!.id, "https://x.invalid")).rejects.toThrow(/administrador/);
    await expect(createResetLink(N.as("director"), O.users.journalist!.id, "https://x.invalid")).rejects.toThrow(/não pertence/);
  });

  it("um link novo anula o anterior; um token inventado não serve", async () => {
    const a = (await createResetLink(N.as("director"), N.users.journalist2!.id, "https://x.invalid")).link.split("/").pop()!;
    const b = (await createResetLink(N.as("director"), N.users.journalist2!.id, "https://x.invalid")).link.split("/").pop()!;
    expect(await resetPassword(a, "palavra-passe-nova-1")).toBe(false);
    expect(await resetPassword(b, "palavra-passe-nova-1")).toBe(true);
    expect(await resetPassword("x".repeat(43), "palavra-passe-nova-1")).toBe(false);
  });
});

describe("biblioteca de média", () => {
  it("reconhece o tipo pelos bytes e recusa o resto (mesmo com nome de imagem)", () => {
    expect(sniffImage(PNG)).toBe("image/png");
    expect(sniffImage(Uint8Array.from([0xff, 0xd8, 0xff, 0xe0, 0]))).toBe("image/jpeg");
    expect(sniffImage(new TextEncoder().encode("<svg onload=alert(1)>"))).toBeNull();
  });

  it("guarda, lista e serve ao público da MESMA publicação; outra publicação não vê", async () => {
    const id = await saveMedia(N.as("journalist"), { bytes: PNG, filename: "ponte.png", width: 1, height: 1, alt: "Ponte", credit: "Ana" });
    const lista = await withCtx(N.as("editor"), (tx) => listMedia(tx));
    expect(lista.find((m) => m.id === id)).toMatchObject({ content_type: "image/png", size: PNG.length, credit: "Ana" });
    expect((await readMedia(publicCtx(N.publicationId), id))?.content_type).toBe("image/png");
    expect(await readMedia(publicCtx(O.publicationId), id)).toBeNull();
    expect(await readMedia(O.as("editor"), id)).toBeNull();
  });

  it("quem só revê não carrega; uma imagem não se substitui por outra", async () => {
    await expect(saveMedia(N.as("reviewer"), { bytes: PNG, filename: "x.png" })).rejects.toThrow();
    const id = await saveMedia(N.as("journalist"), { bytes: PNG, filename: "y.png" });
    await expect(withCtx(N.as("editor"), (tx) => tx`update media set bytes = ${Buffer.from([0xff, 0xd8, 0xff, 0xe0, 1, 2])} where id = ${id}`)).rejects.toThrow(/não se substitui/);
    await withCtx(N.as("editor"), (tx) => tx`update media set credit = 'Rui' where id = ${id}`);
    expect((await ownerDb()`select credit from media where id = ${id}`)[0]!.credit).toBe("Rui");
  });
});

describe("newsletter com consentimento", () => {
  it("inscreve com o texto aceite e a data, anula por link, e só a direção vê a lista", async () => {
    await subscribe(N.publicationId, " Leitora@Exemplo.invalid ", "Aceito receber a newsletter.");
    const lista = await listSubscribers(N.as("director"));
    expect(lista).toHaveLength(1);
    expect(lista[0]).toMatchObject({ email: "leitora@exemplo.invalid", status: "active" });
    expect(await listSubscribers(N.as("editor"))).toEqual([]); // RLS: a edição não vê a lista
    expect(await listSubscribers(O.as("director"))).toEqual([]);
    const csv = subscribersCsv(lista, "https://exemplo.invalid/");
    expect(csv).toContain(`leitora@exemplo.invalid,`);
    expect(csv).toContain(`https://exemplo.invalid/newsletter/anular?t=${lista[0]!.unsubscribe_token}`);
    expect(await unsubscribe(lista[0]!.unsubscribe_token)).toBe(true);
    expect((await listSubscribers(N.as("director")))[0]!.status).toBe("unsubscribed");
    expect(subscribersCsv(await listSubscribers(N.as("director")), "https://x.invalid")).not.toContain("leitora@");
    // voltar a inscrever-se reactiva, com novo consentimento
    await subscribe(N.publicationId, "leitora@exemplo.invalid", "Aceito outra vez.");
    expect((await listSubscribers(N.as("director")))[0]).toMatchObject({ status: "active" });
  });

  it("recusa emails inválidos e inscrições sem consentimento", async () => {
    await expect(subscribe(N.publicationId, "não-é-email", "ok")).rejects.toThrow(/email/);
    await expect(subscribe(N.publicationId, "a@b.invalid", "  ")).rejects.toThrow(/aceitar/);
    expect(await unsubscribe("nao-e-token")).toBe(false);
  });
});

describe("cópia de segurança", () => {
  it("leva o trabalho desta publicação e nenhum segredo; só a direção a pede", async () => {
    await saveMedia(N.as("journalist"), { bytes: PNG, filename: "z.png" });
    const b = await exportPublication(N.as("director"));
    expect(b.format).toBe("editorial-backup/1");
    expect((b.publications as { id: string }[]).map((p) => p.id)).toEqual([N.publicationId]);
    const txt = JSON.stringify(b);
    expect(txt).not.toMatch(/password_hash|scrypt\$|token_hash/);
    expect(txt).not.toContain(O.publicationId);
    expect((b.media as unknown[]).length).toBeGreaterThan(0);
    expect(JSON.stringify(b.media)).not.toContain("bytes");
    await expect(exportPublication(N.as("editor"))).rejects.toThrow(/direção/);
  });
});
