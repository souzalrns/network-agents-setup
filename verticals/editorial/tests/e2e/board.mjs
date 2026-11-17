// Quadro de pautas: arrastar só para destinos permitidos, «Mover para…» sem rato, e a base de dados continua a decidir.
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const BASE = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3100";
const ADMIN = { email: process.env.E2E_ADMIN_EMAIL ?? "direcao@exemplo.invalid", password: process.env.E2E_ADMIN_PASSWORD ?? "redacao-local-123" };
const tag = Date.now().toString(36);
const results = [];
const check = (name, ok, detail = "") => { results.push(ok); console.log(`${ok ? "PASSOU" : "FALHOU"}  ${name}${detail ? `  (${detail})` : ""}`); };

const browser = await chromium.launch();
const errors = [];
try {
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`${r.status()} ${r.url()}`); });
  await page.goto(`${BASE}/redacao/entrar`);
  await page.fill("#email", ADMIN.email); await page.fill("#password", ADMIN.password);
  await page.click("button[type=submit]"); await page.waitForURL(`${BASE}/redacao`);
  const title = `Quadro ${tag}`;
  await page.goto(`${BASE}/redacao/pautas/nova`);
  await page.fill("#title", title);
  await page.locator("button[name=propose][value='1']").click();
  await page.waitForURL(/\/redacao\/pecas\//);

  const board = `${BASE}/redacao/pautas?vista=quadro&estado=todas`;
  await page.goto(board); await page.waitForLoadState("networkidle");
  const tile = () => page.locator(".tile", { hasText: title });
  const col = (name) => page.locator(".col", { has: page.locator("h3", { hasText: name }) });
  check("a pauta proposta está na coluna «Pautas»", (await col("Pautas").locator(".tile", { hasText: title }).count()) === 1);

  // largar numa coluna sem destino permitido não muda nada
  await tile().dragTo(col("Publicadas"));
  await page.waitForTimeout(500);
  check("largar numa coluna não permitida não muda o estado", (await col("Pautas").locator(".tile", { hasText: title }).count()) === 1);

  // largar no banco de ideias: único destino permitido nessa coluna, muda logo
  await Promise.all([page.waitForURL(/ok=/, { timeout: 15_000 }), tile().dragTo(col("Banco de ideias"))]);
  await page.waitForLoadState("networkidle");
  check("arrastar para «Banco de ideias» devolve a pauta a ideia", (await col("Banco de ideias").locator(".tile", { hasText: title }).count()) === 1,
    (await page.locator(".flash").allTextContents()).join(" | "));
  check("e volta ao quadro com a confirmação", page.url().includes("vista=quadro") && (await page.locator(".flash").allTextContents()).join(" ").includes("passou a Ideia"));

  // sem rato: «Mover para…»
  await page.goto(board); await page.waitForLoadState("networkidle");
  await tile().locator("select[name=to]").selectOption("pitch_proposed");
  await Promise.all([page.waitForURL(/ok=/, { timeout: 15_000 }), tile().locator("button", { hasText: "Mover" }).click()]);
  await page.waitForLoadState("networkidle");
  check("«Mover para…» faz o mesmo sem arrastar", (await col("Pautas").locator(".tile", { hasText: title }).count()) === 1);

  // dentro da coluna «Pautas» há dois destinos para a direção: aprovar ou voltar a ideia; o quadro pergunta
  const targets = await tile().locator("select[name=to] option").allTextContents();
  check("o cartão só oferece os passos que o fluxo permite", targets.includes("Aprovar pauta") && !targets.some((t) => /Publicar|Aprovar$/.test(t)), targets.join(", "));

  // telemóvel: o quadro desliza na horizontal sem transbordar a página
  const m = await browser.newContext({ viewport: { width: 400, height: 800 }, hasTouch: true, storageState: await ctx.storageState() });
  const mp = await m.newPage();
  await mp.goto(board); await mp.waitForLoadState("networkidle");
  const over = await mp.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check("no telemóvel o quadro não transborda a página", over === 0, `+${over}px`);
  check("no telemóvel cada cartão tem «Mover para…»", (await mp.locator(".tile select[name=to]").count()) > 0);
  await m.close();
  check("sem erros de servidor nem de página", errors.length === 0, errors.slice(0, 3).join(" | "));
} catch (e) {
  check("o percurso terminou sem exceção", false, String(e?.message ?? e).slice(0, 300));
} finally {
  await browser.close();
}
const failed = results.filter((x) => !x).length;
console.log(`\n${results.length - failed}/${results.length} verificações passaram`);
process.exit(failed ? 1 : 0);
