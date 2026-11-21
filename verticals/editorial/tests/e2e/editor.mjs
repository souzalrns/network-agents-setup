// Editor no browser, com duas pessoas: autosave no servidor, recuperação depois de recarregar, conflito
// entre duas pessoas sem perda de texto, versão guardada, barra de formatação, pré-visualização, comparação
// e restauro de versões. Corre dentro de all.mjs (base própria).
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const BASE = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3100";
const ADMIN = { email: process.env.E2E_ADMIN_EMAIL ?? "direcao@exemplo.invalid", password: process.env.E2E_ADMIN_PASSWORD ?? "redacao-local-123" };
const tag = Date.now().toString(36);
const B = { name: `Segunda ${tag}`, email: `segunda-${tag}@exemplo.invalid`, password: "palavra-passe-segunda" };
const results = [];
const check = (name, ok, detail = "") => { results.push(ok); console.log(`${ok ? "PASSOU" : "FALHOU"}  ${name}${detail ? `  (${detail})` : ""}`); };

const browser = await chromium.launch();
const errors = [];
async function person(who) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`${r.status()} ${r.url()}`); if (process.env.E2E_DEBUG && r.url().includes("rascunho")) console.log("debug", r.status(), r.url()); });
  await page.goto(`${BASE}/redacao/entrar`);
  await page.fill("#email", who.email); await page.fill("#password", who.password);
  await page.click("button[type=submit]"); await page.waitForURL(`${BASE}/redacao`);
  return page;
}
async function act(page, locator) {
  const before = page.url();
  await Promise.all([
    page.waitForURL((u) => u.href !== before && /[?&](ok|erro)=/.test(u.href), { timeout: 20_000 }).catch(() => {}),
    locator.click(),
  ]);
  await page.waitForLoadState("networkidle");
}
const flash = async (page) => (await page.locator(".flash").allTextContents()).join(" | ");
const status = (page) => page.locator(".autosave").textContent();
const waitSaved = (page) => page.waitForFunction(() => /guardado no servidor/.test(document.querySelector(".autosave")?.textContent ?? ""), null, { timeout: 15_000 })
  .catch(async (e) => { throw new Error(`autosave sem confirmação: «${await page.locator(".autosave").textContent().catch(() => "?")}»`); });
const version = async (page) => Number((await page.locator(".nr-head .meta").textContent()).match(/Versão (\d+)/)[1]);

try {
  const a = await person(ADMIN);
  // segunda pessoa da edição
  await a.goto(`${BASE}/redacao/equipa`);
  await a.fill("#m-name", B.name); await a.fill("#m-email", B.email); await a.selectOption("#m-role", "editor"); await a.fill("#m-pass", B.password);
  await act(a, a.locator("text=Acrescentar à equipa"));

  // uma peça em redacção
  await a.goto(`${BASE}/redacao/pautas/nova`);
  await a.fill("#title", `Peça do editor ${tag}`);
  await a.locator("button[name=propose][value='1']").click();
  await a.waitForURL(/\/redacao\/pecas\//);
  const url = a.url().split("?")[0].split("#")[0];
  for (const step of ["Aprovar pauta", "Começar a escrever"]) {
    await act(a, a.locator(".side form button", { hasText: new RegExp(`^${step}$`) }).first());
  }
  const v0 = await version(a);

  // 1. autosave: escreve, espera, recarrega e o texto continua lá, sem criar versão
  await a.fill("#a-body", `Primeiro parágrafo ${tag}.\n\nSegundo parágrafo.`);
  await waitSaved(a);
  check("o autosave grava no servidor depois de parar de escrever", /guardado no servidor/.test(await status(a)), await status(a));
  await a.reload(); await a.waitForLoadState("networkidle");
  check("depois de recarregar, o texto volta do rascunho do servidor", (await a.inputValue("#a-body")).includes(`Primeiro parágrafo ${tag}`));
  check("o autosave não cria versões", (await version(a)) === v0, `v${await version(a)}`);

  // 2. barra de formatação e pré-visualização ao lado (HTML do servidor, o mesmo do site)
  await a.locator("#a-body").evaluate((el) => { el.focus(); el.setSelectionRange(0, 8); });
  await a.locator(".toolbar button[title^='Negrito']").click();
  check("o botão de negrito envolve a selecção", (await a.inputValue("#a-body")).startsWith("**Primeiro**"));
  await a.locator(".toolbar button[title='Intertítulo']").click();
  await a.locator(".toolbar label.check input").check();
  await a.waitForFunction(() => !!document.querySelector(".preview-live h2, .preview-live strong"), null, { timeout: 10_000 });
  check("a pré-visualização ao lado mostra a formatação", (await a.locator(".preview-live strong").count()) > 0);
  await a.locator(".toolbar-pop summary").click();
  await a.locator(".toolbar-pop input").nth(1).fill("https://exemplo.invalid/foto.jpg");
  await a.locator(".toolbar-pop input").nth(2).fill("A ponte ao fim da tarde");
  await a.locator(".toolbar-pop input").nth(3).fill("Ana Silva");
  await a.locator(".toolbar-pop button", { hasText: "Inserir figura" }).click();
  check("inserir figura escreve legenda e crédito no dialecto", (await a.inputValue("#a-body")).includes('![A ponte ao fim da tarde](https://exemplo.invalid/foto.jpg "Ana Silva")'));
  await a.waitForFunction(() => !!document.querySelector(".preview-live figcaption"), null, { timeout: 10_000 });
  check("a figura aparece com legenda e crédito na pré-visualização", (await a.locator(".preview-live figcaption").textContent()).includes("Fotografia: Ana Silva"));
  await waitSaved(a);

  // 3. a segunda pessoa abre a mesma peça: vê o aviso e, se escrever por cima, tem conflito
  const b = await person(B);
  await b.goto(url); await b.waitForLoadState("networkidle");
  check("a segunda pessoa vê que há um rascunho por guardar de outra pessoa", (await b.locator(".notice-box", { hasText: "tem um rascunho por guardar" }).count()) === 1);
  check("e é avisada de que a outra pessoa está a editar", (await b.locator(".flash.erro", { hasText: "está a editar" }).count()) === 1);
  await b.fill("#a-body", `Texto da segunda pessoa ${tag}.`);
  await b.waitForSelector(".notice-box.warn[role=alert]", { timeout: 15_000 });
  check("o autosave da segunda pessoa dá conflito em vez de sobrepor", (await b.locator(".notice-box.warn[role=alert]").textContent()).includes("Nada foi sobreposto"));
  await a.reload(); await a.waitForLoadState("networkidle");
  check("o rascunho da primeira pessoa ficou intacto", (await a.inputValue("#a-body")).includes(`Primeiro parágrafo ${tag}`) || (await a.inputValue("#a-body")).includes("**Primeiro**"));

  // 4. a primeira guarda a versão; o texto da segunda continua recuperável no browser dela
  await a.fill("#a-note", "primeira versão do editor");
  await act(a, a.locator(".save-bar button[type=submit]"));
  check("guardar versão cria uma versão nova", (await flash(a)).includes("Versão guardada") && (await version(a)) === v0 + 1, await flash(a));
  await b.reload(); await b.waitForLoadState("networkidle");
  check("a segunda pessoa recupera o texto que o servidor nunca recebeu", (await b.locator(".notice-box", { hasText: "nunca recebeu" }).count()) === 1);
  await b.locator(".notice-box button", { hasText: "Recuperar esse texto" }).click();
  await b.waitForSelector(".notice-box.warn", { timeout: 15_000 });
  check("e é avisada de que a peça mudou de versão entretanto (não grava por cima)", (await b.locator(".notice-box.warn").first().textContent()).includes(`já vai na versão ${v0 + 1}`));
  await b.locator(".save-bar button[type=submit]").click();
  await b.waitForURL(/erro=/, { timeout: 15_000 }).catch(() => {});
  check("guardar versão sobre uma versão antiga é recusado", (await flash(b)).includes("Outra pessoa guardou a versão"), await flash(b));

  // 5. comparação e restauro
  await a.fill("#a-body", "Texto completamente novo.");
  await act(a, a.locator(".save-bar button[type=submit]"));
  await a.goto(`${url}/versoes`);
  check("a página de versões compara palavra a palavra", (await a.locator(".diff ins").count()) > 0 && (await a.locator(".diff del").count()) > 0);
  await act(a, a.locator("form button", { hasText: "Restaurar como nova versão" }).nth(1));
  check("restaurar cria uma versão nova", (await flash(a)).includes("restaurada como versão"), await flash(a));

  // 6. pré-visualização fiel
  await a.goto(`${BASE}/redacao/pre-visualizar/${url.split("/").pop()}`);
  check("a pré-visualização fiel usa o artigo do site", (await a.locator("article.article h1").count()) === 1 && (await a.locator(".preview-bar").count()) === 1);
  check("sem erros de servidor nem de página", errors.length === 0, errors.slice(0, 3).join(" | "));
} catch (e) {
  check("o percurso terminou sem exceção", false, String(e?.message ?? e).slice(0, 300));
} finally {
  await browser.close();
}
const failed = results.filter((x) => !x).length;
console.log(`\n${results.length - failed}/${results.length} verificações passaram`);
process.exit(failed ? 1 : 0);
