// O dialecto do artigo (figuras, vídeos) e a higienização: o mesmo HTML na pré-visualização e no site.
import { describe, expect, it } from "vitest";
import { renderMarkdown } from "@/lib/markdown";

describe("dialecto do artigo", () => {
  it("uma imagem sozinha vira figura com legenda e crédito", () => {
    const h = renderMarkdown('Antes.\n\n![A ponte de Santa Clara](https://exemplo.invalid/ponte.jpg "Ana Silva")\n\nDepois.');
    expect(h).toContain("<figure><img");
    expect(h).toContain("<figcaption>A ponte de Santa Clara Fotografia: Ana Silva</figcaption>");
  });

  it("um endereço do YouTube sozinho numa linha vira vídeo sem cookies; outros iframes não passam", () => {
    const h = renderMarkdown("Veja:\n\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\n\nFim.");
    expect(h).toContain('src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"');
    expect(renderMarkdown('<iframe src="https://mau.invalid/x"></iframe>')).not.toContain("mau.invalid");
    // nem páginas do próprio site (a redacção dentro de um artigo público)
    expect(renderMarkdown('<iframe src="/redacao/entrar"></iframe>')).not.toContain("/redacao");
  });

  it("continua a retirar scripts, eventos e esquemas perigosos", () => {
    const h = renderMarkdown('<script>alert(1)</script>[x](javascript:alert(1)) <img src="x" onerror="alert(1)">');
    expect(h).not.toMatch(/<script|href="javascript:|onerror/);
  });
});
