// Medições de telemóvel e computador (critérios do P0): sem transbordo horizontal em 360/400/768/1280 px,
// cabeçalho da redacção até 64 px em 400 px, menu móvel num <dialog> que abre, prende o foco e fecha com Esc,
// e a página da equipa curta (uma linha por pessoa).
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const BASE = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3100";
const ADMIN = { email: process.env.E2E_ADMIN_EMAIL ?? "direcao@exemplo.invalid", password: process.env.E2E_ADMIN_PASSWORD ?? "redacao-local-123" };
const results = [];
const check = (name, ok, detail = "") => { results.push(ok); console.log(`${ok ? "PASSOU" : "FALHOU"}  ${name}${detail ? `  (${detail})` : ""}`); };

const browser = await chromium.launch();
try {
  for (const width of [360, 400, 768, 1280]) {
    const ctx = await browser.newContext({ viewport: { width, height: 800 }, deviceScaleFactor: 1, hasTouch: width < 800 });
    const page = await ctx.newPage();
    await page.goto(`${BASE}/redacao/entrar`);
    await page.fill("#email", ADMIN.email); await page.fill("#password", ADMIN.password);
    await page.click("button[type=submit]"); await page.waitForURL(`${BASE}/redacao`);
    await page.goto(`${BASE}/redacao/pautas?estado=todas`);
    const story = await page.locator(".card .item-title").first().getAttribute("href");
    const pages = ["/redacao", "/redacao/pautas", "/redacao/pautas?vista=quadro&estado=todas", story, "/redacao/calendario",
      "/redacao/fontes", "/redacao/equipa", "/redacao/radar", "/redacao/configuracao", "/redacao/atividade", `${story}/versoes`, "/", "/sobre"];
    const over = [];
    for (const url of pages) {
      await page.goto(`${BASE}${url}`); await page.waitForLoadState("networkidle");
      const d = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (d > 0) over.push(`${url} +${d}px`);
    }
    check(`sem transbordo horizontal a ${width}px (${pages.length} páginas)`, over.length === 0, over.join(", "));
    await page.goto(`${BASE}/redacao/equipa`);
    const h = await page.evaluate(() => ({ header: Math.round(document.querySelector(".nr-top").getBoundingClientRect().height), page: document.documentElement.scrollHeight }));
    if (width === 400) {
      check("cabeçalho da redação ≤ 64px a 400px", h.header <= 64, `${h.header}px`);
      check("página da equipa ≤ 2000px a 400px", h.page <= 2000, `${h.page}px`);
      const btn = page.locator(".nr-menu-btn");
      check("botão de menu visível no telemóvel", await btn.isVisible());
      await btn.click();
      const open = await page.evaluate(() => document.querySelector(".nr-dialog")?.open === true);
      check("o menu abre num <dialog> modal", open);
      const inside = await page.evaluate(() => !!document.activeElement?.closest(".nr-dialog"));
      check("o foco fica dentro do menu", inside);
      await page.keyboard.press("Escape");
      check("Esc fecha o menu", await page.evaluate(() => document.querySelector(".nr-dialog")?.open === false));
      await btn.click();
      await page.locator(".nr-dialog nav a", { hasText: "Calendário" }).click();
      await page.waitForURL(/calendario/);
      check("escolher uma página no menu navega e fecha o menu", await page.evaluate(() => document.querySelector(".nr-dialog")?.open === false));
    }
    if (width === 1280) check("no computador a barra de navegação está visível e o botão de menu não", await page.locator(".nr-nav").isVisible() && !(await page.locator(".nr-menu-btn").isVisible()));
    await ctx.close();
  }
} catch (e) {
  check("execução sem excepções", false, e.message);
} finally {
  await browser.close();
}
const failed = results.filter((x) => !x).length;
console.log(`\n${results.length - failed}/${results.length} verificações passaram`);
process.exit(failed ? 1 : 0);
