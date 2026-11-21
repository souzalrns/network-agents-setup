// Operação da redação sem serviços externos: link de recuperação, biblioteca de média, newsletter e cópia de segurança.
import { createRequire } from "node:module";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const BASE = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3100";
const ADMIN = { email: process.env.E2E_ADMIN_EMAIL ?? "direcao@exemplo.invalid", password: process.env.E2E_ADMIN_PASSWORD ?? "redacao-local-123" };
const tag = Date.now().toString(36);
const P = { name: `Recuperada ${tag}`, email: `recuperada-${tag}@exemplo.invalid`, password: "palavra-passe-inicial" };
const results = [];
const check = (name, ok, detail = "") => { results.push(ok); console.log(`${ok ? "PASSOU" : "FALHOU"}  ${name}${detail ? `  (${detail})` : ""}`); };

const dir = mkdtempSync(join(tmpdir(), "e2e-img-"));
const png = join(dir, "ponte.png");
writeFileSync(png, Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==", "base64"));

const browser = await chromium.launch();
const errors = [];
async function context() {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`${r.status()} ${r.url()}`); });
  return { ctx, page };
}
async function login(page, who) {
  await page.goto(`${BASE}/redacao/entrar`);
  await page.fill("#email", who.email); await page.fill("#password", who.password);
  await page.click("button[type=submit]"); await page.waitForURL(`${BASE}/redacao`, { timeout: 15_000 });
}
// pedidos feitos DENTRO da página (como o utilizador): o cookie de sessão é «secure» e o pedido directo do
// Playwright para http://127.0.0.1 não o envia, o browser sim
const inPage = (page, url) => page.evaluate(async (u) => { const r = await fetch(u); return { status: r.status, text: await r.text() }; }, url);
const flash = async (page) => (await page.locator(".flash").allTextContents()).join(" | ");

try {
  const { page: a } = await context();
  await login(a, ADMIN);

  // 1. link de recuperação
  await a.goto(`${BASE}/redacao/equipa`);
  await a.fill("#m-name", P.name); await a.fill("#m-email", P.email); await a.selectOption("#m-role", "journalist"); await a.fill("#m-pass", P.password);
  await Promise.all([a.waitForURL(/ok=/), a.locator("text=Acrescentar à equipa").click()]);
  await a.goto(`${BASE}/redacao/equipa`);
  await a.locator("tr", { hasText: P.name }).locator("a", { hasText: "Editar" }).click();
  await a.waitForURL(/\/redacao\/equipa\//);
  await a.locator("button", { hasText: "Gerar link de recuperação" }).click();
  const linkBox = a.locator("input[aria-label='Link de recuperação']");
  await linkBox.waitFor({ timeout: 15_000 });
  const link = await linkBox.inputValue();
  check("a direção gera um link de recuperação de uso único", /\/redacao\/recuperar\/[\w-]{40,}$/.test(link), link.replace(/[\w-]{40,}$/, "…"));
  check("o link não vai no endereço da página", !a.url().includes("recuperar"));
  const { page: b } = await context();
  await b.goto(link.replace(/^https?:\/\/[^/]+/, BASE));
  await b.fill("#password", "palavra-passe-recuperada"); await b.fill("#confirm", "palavra-passe-recuperada");
  await Promise.all([b.waitForURL(/entrar\?ok=/), b.locator("button[type=submit]").click()]);
  check("a pessoa escolhe uma palavra-passe nova pelo link", (await flash(b)).includes("Palavra-passe alterada"), await flash(b));
  await login(b, { email: P.email, password: "palavra-passe-recuperada" });
  check("e entra com ela", b.url().endsWith("/redacao"));
  await b.goto(link.replace(/^https?:\/\/[^/]+/, BASE));
  await b.fill("#password", "terceira-palavra-passe"); await b.fill("#confirm", "terceira-palavra-passe");
  await Promise.all([b.waitForURL(/erro=/), b.locator("button[type=submit]").click()]);
  check("o mesmo link não serve duas vezes", (await flash(b)).includes("já foi usado"), await flash(b));

  // 2. biblioteca de média
  await a.goto(`${BASE}/redacao/media`);
  await a.fill("#u-alt", "A ponte"); await a.fill("#u-credit", "Ana Silva");
  await a.setInputFiles("#u-file", png);
  await a.waitForSelector(".flash.ok", { timeout: 20_000 });
  await a.waitForSelector(".media-item img", { timeout: 15_000 });
  const src = await a.locator(".media-item img").first().getAttribute("src");
  check("carregar uma imagem põe-na na biblioteca com legenda e crédito", /^\/media\/[0-9a-f-]{36}$/.test(src ?? "") && (await a.locator(".media-md").first().textContent()).includes('"Ana Silva"'), src ?? "");
  const pub = await (await browser.newContext()).request.get(`${BASE}${src}`);
  check("o site serve a imagem ao público, com o tipo certo e cache longa", pub.status() === 200 && pub.headers()["content-type"] === "image/png" && /immutable/.test(pub.headers()["cache-control"] ?? ""));

  // 3. newsletter
  const { page: r } = await context();
  await r.goto(`${BASE}/`);
  await r.fill("#nl-email", `leitora-${tag}@exemplo.invalid`);
  await r.locator("#newsletter input[name=consent]").check();
  await Promise.all([r.waitForURL(/newsletter\?estado=ok/), r.locator("#newsletter button[type=submit]").click()]);
  check("um leitor inscreve-se na newsletter a partir do rodapé, com consentimento", (await flash(r)).includes("Inscrição feita"));
  await a.goto(`${BASE}/redacao/newsletter`);
  check("a direção vê a inscrição", (await a.locator("table.t", { hasText: `leitora-${tag}@exemplo.invalid` }).count()) === 1);
  const csv = await inPage(a, "/redacao/exportar/newsletter");
  const csvText = csv.text;
  csv.status = ((st) => () => st)(csv.status);
  check("exporta as inscrições ativas em CSV com o link de anulação", csv.status() === 200 && csvText.includes(`leitora-${tag}@exemplo.invalid`) && csvText.includes("/newsletter/anular?t="), `${csv.status()} ${csvText.slice(0, 160).replace(/\n/g, " / ")}`);
  const unsub = csvText.split("\n").find((l) => l.includes(`leitora-${tag}`)).split(",").pop();
  await r.goto(unsub.replace(/^https?:\/\/[^/]+/, BASE));
  check("o link de anulação anula a inscrição", (await r.locator("h1").textContent()).includes("anulada"));

  // 4. cópia de segurança
  const backup = await inPage(a, "/redacao/exportar/copia");
  const json = JSON.parse(backup.text);
  check("a direção descarrega a cópia de segurança, sem segredos", backup.status === 200 && json.format === "editorial-backup/1" && !backup.text.includes("scrypt$"));
  const denied = await inPage(b, "/redacao/exportar/copia");
  check("uma jornalista não descarrega a cópia", denied.status === 403, String(denied.status));
  check("sem erros de servidor nem de página", errors.length === 0, errors.slice(0, 3).join(" | "));
} catch (e) {
  check("o percurso terminou sem exceção", false, String(e?.message ?? e).slice(0, 300));
} finally {
  await browser.close();
}
const failed = results.filter((x) => !x).length;
console.log(`\n${results.length - failed}/${results.length} verificações passaram`);
process.exit(failed ? 1 : 0);
