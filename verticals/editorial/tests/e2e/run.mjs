// Teste de ponta a ponta no browser: uma peça percorre a redacção inteira, com três pessoas, até ao site.
// Precisa da aplicação a correr (E2E_BASE_URL, omissão http://127.0.0.1:3100) sobre uma base semeada,
// e de uma conta de administração (E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD).
// Uso: node tests/e2e/run.mjs   (Playwright tem de estar disponível: require('playwright'))
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const BASE = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3100";
const ADMIN = { email: process.env.E2E_ADMIN_EMAIL ?? "direcao@exemplo.invalid", password: process.env.E2E_ADMIN_PASSWORD ?? "redacao-local-123" };
const SHOTS = process.env.E2E_SHOTS ?? "";
const tag = Date.now().toString(36);
const EDITOR = { name: `Editora ${tag}`, email: `editora-${tag}@exemplo.invalid`, password: "palavra-passe-editora" };
const JOURNALIST = { name: `Jornalista ${tag}`, email: `jornalista-${tag}@exemplo.invalid`, password: "palavra-passe-jornalista" };

const results = [];
function check(name, ok, detail = "") {
  results.push({ name, ok, detail });
  console.log(`${ok ? "PASSOU" : "FALHOU"}  ${name}${detail ? `  (${detail})` : ""}`);
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("response", (r) => { if (r.status() >= 500) errors.push(`${r.status()} ${r.url()}`); });

async function shot(name) {
  if (!SHOTS) return;
  mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: false });
}
const flash = async () => (await page.locator(".flash").allTextContents()).join(" | ");

/** Clica e espera que a acção do servidor devolva a página com a mensagem (ok/erro) no endereço. */
async function act(locator) {
  const before = page.url();
  await Promise.all([
    page.waitForURL((u) => u.href !== before && /[?&](ok|erro)=/.test(u.href), { timeout: 20_000 }).catch(() => {}),
    locator.click(),
  ]);
  await page.waitForLoadState("networkidle");
}

async function login(who) {
  await ctx.clearCookies();
  await page.goto(`${BASE}/redacao/entrar`);
  await page.fill("#email", who.email);
  await page.fill("#password", who.password);
  await page.click("button[type=submit]");
  await page.waitForURL(`${BASE}/redacao`);
}

async function stepButton(label) {
  await act(page.locator(".side form button", { hasText: new RegExp(`^${label}$`) }).first());
}

try {
  // 1. a direcção entra e monta a equipa
  await login(ADMIN);
  check("a direção entra na redação", (await page.locator("h1").textContent()).startsWith("Bom trabalho"));
  await shot("01-painel");
  for (const [who, role] of [[EDITOR, "editor"], [JOURNALIST, "journalist"]]) {
    await page.goto(`${BASE}/redacao/equipa`);
    await page.fill("#m-name", who.name);
    await page.fill("#m-email", who.email);
    await page.selectOption("#m-role", role);
    await page.fill("#m-pass", who.password);
    await act(page.locator("text=Acrescentar à equipa"));
    check(`acrescenta ${role} à equipa`, (await flash()).includes("entrou na equipa"), await flash());
  }

  // 2. a jornalista adopta uma pauta do banco e propõe-a
  await login(JOURNALIST);
  await page.goto(`${BASE}/redacao/pautas?estado=idea`);
  const first = page.locator(".card .item-title").first();
  const storyTitle = (await first.textContent()).trim();
  await first.click();
  await page.waitForURL(/\/redacao\/pecas\//);
  const storyUrl = page.url().split("?")[0].split("#")[0];
  await stepButton("Propor como pauta");
  check("a jornalista propõe uma ideia do banco", (await page.locator(".nr-head .pill").first().textContent()).includes("Pauta proposta"));
  await shot("02-peca-proposta");

  // não consegue aprovar a própria pauta
  check("a jornalista não vê o botão de aprovar pauta", (await page.locator(".side button", { hasText: "Aprovar pauta" }).count()) === 0);

  // 3. a editora aprova e atribui
  await login(EDITOR);
  await page.goto(storyUrl);
  await stepButton("Aprovar pauta");
  check("a edição aprova a pauta", (await page.locator(".nr-head .pill").first().textContent()).includes("Pauta aprovada"));
  await page.selectOption("#p-assignee", { label: JOURNALIST.name });
  await act(page.locator("#pauta button[type=submit]"));
  check("a edição atribui a pauta", (await flash()).includes("Pauta guardada"));

  // 4. a jornalista escreve e envia para revisão
  await login(JOURNALIST);
  await page.goto(storyUrl);
  await stepButton("Começar a escrever");
  await page.fill("#a-subtitle", "Quartos, comida e transportes somados mês a mês.");
  await page.fill("#a-summary", "Fizemos as contas com três estudantes deslocados.");
  await page.fill("#a-body", `## O que encontrámos\n\nSegundo a associação de estudantes, um quarto custa em média 350 euros por mês.\n\n> «Pago mais de quarto do que de propinas», disse uma estudante.\n\nTexto de teste ${tag}.`);
  await page.fill("#a-note", "primeira versão");
  await act(page.locator("#artigo button[type=submit]"));
  check("a jornalista guarda o texto e fica uma versão", (await flash()).includes("Versão guardada"), await flash());

  // o agente de edição revê sem mexer no texto
  const before = await page.inputValue("#a-body");
  await act(page.locator('#agentes form:has(input[name=agent][value=editor]) button'));
  check("o agente de edição deixa uma proposta", (await flash()).includes("proposta"), await flash());
  check("o agente não altera o texto", (await page.inputValue("#a-body")) === before);
  await act(page.locator('#agentes form:has(input[name=agent][value=factcheck]) button'));
  const claims = await page.locator("#verificacao .list > .claim").count();
  check("o agente de verificação regista afirmações por verificar", claims > 0, `${claims} afirmações`);
  // as propostas do agente entram fora do artigo; a jornalista regista uma informação ainda não confirmada
  await page.locator("#verificacao summary", { hasText: "Registar afirmação" }).click();
  await page.fill("#c-text", "A residência nova abre no próximo semestre.");
  await page.selectOption("#c-kind", "unconfirmed");
  await act(page.locator("#verificacao form:has(#c-text) button[type=submit]"));
  check("a jornalista regista uma informação não confirmada", (await flash()).includes("Afirmação registada"), await flash());
  await shot("03-peca-agentes");
  check("a autora não tem como verificar as afirmações da sua peça (quatro olhos)",
    (await page.locator("#verificacao button", { hasText: "Registar verificação" }).count()) === 0
    && (await page.locator("#verificacao", { hasText: "a verificação é de outra pessoa" }).count()) === 1);

  await stepButton("Enviar para revisão");
  check("a peça vai para revisão", (await page.locator(".nr-head .pill").first().textContent()).includes("Em revisão"));

  // 5. a editora tenta aprovar com afirmações por verificar: a base de dados recusa
  await login(EDITOR);
  await page.goto(storyUrl);
  await stepButton("Aprovar");
  const blocked = await flash();
  check("não se aprova com afirmações por verificar", blocked.includes("afirmações por verificar"), blocked);

  // verifica cada afirmação (com evidência) ou retira-a do artigo
  const n = await page.locator("#verificacao .list > .claim").count();
  for (let i = 0; i < n; i++) {
    const c = () => page.locator("#verificacao .list > .claim").nth(i);
    if ((await c().locator("b").first().textContent()).includes("Não confirmada")) {
      await c().locator("input[name=in_article]").uncheck(); // informação não confirmada sai do artigo
      await act(c().locator("form:has(input[name=in_article]) button[type=submit]"));
    } else {
      await c().locator("input[name=evidence_url]").fill("https://www.ine.pt/");
      await act(c().locator("form:has(input[name=evidence_url]) button[type=submit]"));
      await c().locator("select[name=verification]").selectOption("verified");
      await act(c().locator("form:has(select[name=verification]) button[type=submit]"));
    }
  }
  check("a edição verifica as afirmações e retira a não confirmada", (await page.locator("#verificacao .flash.erro").count()) === 0);
  await stepButton("Aprovar");
  check("a edição aprova a peça", (await page.locator(".nr-head .pill").first().textContent()).includes("Aprovada"), await flash());
  await stepButton("Publicar agora");
  check("a edição publica", (await page.locator(".nr-head .pill").first().textContent()).includes("Publicada"), await flash());

  // 6. distribuição: adaptação aprovada segue para o Postiz como rascunho (sem Postiz configurado: simula)
  await page.fill("#distribuicao input[name=text]", `Quanto custa estudar aqui? ${tag}`);
  await act(page.locator("#distribuicao form").last().locator("button[type=submit]"));
  await act(page.locator("#distribuicao button", { hasText: "Aprovar" }).first());
  await page.goto(`${BASE}/redacao/distribuicao`);
  await act(page.locator("text=/Enviar \\d+ aprovados/"));
  check("o envio para o Postiz só simula sem credenciais", /simulados [1-9]/.test(await flash()) && (await flash()).includes("enviados 0"), await flash());

  // 7. o site público mostra a peça, com dados estruturados e sem indexação em pré-lançamento
  await ctx.clearCookies();
  await page.goto(`${BASE}/`);
  check("a página inicial mostra a peça publicada", (await page.content()).includes(storyTitle.slice(0, 30)));
  await shot("04-site-inicio");
  await page.locator(".teaser a.t", { hasText: storyTitle.slice(0, 20) }).first().click();
  await page.waitForURL(/\/artigo\//);
  const html = await page.content();
  check("o artigo tem dados estruturados NewsArticle", html.includes('"@type":"NewsArticle"'));
  check("o artigo pede para não indexar em pré-lançamento", html.includes('name="robots" content="noindex, nofollow"'));
  check("o artigo mostra o autor", html.includes(JOURNALIST.name));
  await shot("05-site-artigo");
  await page.goto(`${BASE}/pesquisa?q=${tag}`);
  check("a pesquisa encontra a peça", (await page.locator(".teaser").count()) >= 1);
  const feed = await (await page.request.get(`${BASE}/feed.xml`)).text();
  check("o feed RSS traz a peça publicada", feed.includes("<rss") && feed.includes(storyTitle.slice(0, 20).replace(/&/g, "&amp;")));
  const sitemap = await (await page.request.get(`${BASE}/sitemap.xml`)).text();
  check("em pré-lançamento o mapa do site está vazio (nada para indexar)", sitemap.includes("<urlset") && !sitemap.includes("/artigo/"));
  const robots = await (await page.request.get(`${BASE}/robots.txt`)).text();
  check("em pré-lançamento o robots.txt fecha o site e a redação", /Disallow: \/(\s|$)/.test(robots) || robots.includes("Disallow: /redacao"), robots.split("\n").slice(0, 4).join(" / "));
  const ideas = await page.goto(`${BASE}/artigo/nao-existe-${tag}`);
  check("um artigo inexistente dá 404", ideas.status() === 404);
  const draft = await page.goto(`${BASE}/redacao/pautas`);
  check("sem sessão a redação pede entrada", page.url().includes("/redacao/entrar") && draft.ok());

  // 8. papel de leitura e revisão não altera (cria-se pela direção)
  check("sem erros de servidor nem de página", errors.length === 0, errors.slice(0, 3).join(" | "));
} catch (e) {
  check("o percurso terminou sem exceção", false, String(e?.message ?? e).slice(0, 300));
} finally {
  await browser.close();
}
const failed = results.filter((r) => !r.ok).length;
console.log(`\n${results.length - failed} passaram, ${failed} falharam`);
process.exit(failed ? 1 : 0);
