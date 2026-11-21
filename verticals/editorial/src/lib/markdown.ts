import { marked } from "marked";
import sanitizeHtml from "sanitize-html";

marked.setOptions({ gfm: true, breaks: false });

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/**
 * Dialecto do artigo, sobre Markdown (D2), igual na redacção e no site:
 * - figura: uma imagem sozinha num parágrafo, `![Legenda](https://… "Crédito")`, vira <figure> com legenda e crédito;
 * - vídeo: um endereço do YouTube ou do Vimeo sozinho numa linha vira um vídeo incorporado (sem cookies no YouTube).
 */
function dialect(md: string): string {
  return (md ?? "").split("\n").map((line) => {
    const t = line.trim();
    const yt = t.match(/^https:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,20})(?:[&?#]\S*)?$/);
    if (yt) return `<figure class="embed"><iframe src="https://www.youtube-nocookie.com/embed/${yt[1]}" title="Vídeo" loading="lazy" allowfullscreen></iframe></figure>`;
    const vm = t.match(/^https:\/\/(?:www\.)?vimeo\.com\/(\d{4,12})$/);
    if (vm) return `<figure class="embed"><iframe src="https://player.vimeo.com/video/${vm[1]}" title="Vídeo" loading="lazy" allowfullscreen></iframe></figure>`;
    return line;
  }).join("\n");
}

function figures(html: string): string {
  return html.replace(/<p>\s*<img src="([^"]+)" alt="([^"]*)"(?: title="([^"]*)")?\s*\/?>\s*<\/p>/g, (_m, src: string, alt: string, credit?: string) => {
    const cap = [alt, credit ? `Fotografia: ${credit}` : ""].filter(Boolean).join(" ");
    return `<figure><img src="${src}" alt="${alt}">${cap ? `<figcaption>${cap}</figcaption>` : ""}</figure>`;
  });
}

/** Texto do artigo (Markdown) para HTML seguro: só etiquetas de texto, ligações, imagens http(s) e vídeos de dois anfitriões. */
export function renderMarkdown(md: string): string {
  const raw = figures(marked.parse(dialect(md), { async: false }) as string);
  return sanitizeHtml(raw, {
    allowedTags: ["p", "h2", "h3", "h4", "blockquote", "ul", "ol", "li", "strong", "em", "a", "br", "hr",
      "figure", "figcaption", "img", "code", "pre", "table", "thead", "tbody", "tr", "th", "td", "sup", "sub", "iframe"],
    allowedAttributes: { a: ["href", "title", "rel", "target"], img: ["src", "alt", "title", "width", "height", "loading"],
      figure: ["class"], iframe: ["src", "title", "loading", "allowfullscreen"] },
    allowedClasses: { figure: ["embed"] },
    allowedSchemes: ["http", "https", "mailto"],
    allowedIframeHostnames: ["www.youtube-nocookie.com", "player.vimeo.com"],
    // sem isto, <iframe src="/redacao"> passava (endereços relativos ao próprio site são aceites por omissão)
    allowIframeRelativeUrls: false,
    transformTags: {
      a: (tag, attribs) => ({ tagName: tag, attribs: { ...attribs, rel: "noopener noreferrer", ...(attribs.href?.startsWith("http") ? { target: "_blank" } : {}) } }),
      img: (tag, attribs) => ({ tagName: tag, attribs: { ...attribs, loading: "lazy" } }),
      h1: "h2",
    },
  });
}

/** Texto simples (para descrições e contagem de palavras). */
export function plainText(md: string): string {
  return sanitizeHtml(marked.parse(md ?? "", { async: false }) as string, { allowedTags: [], allowedAttributes: {} })
    .replace(/\s+/g, " ").trim();
}

export function readingMinutes(md: string): number {
  return Math.max(1, Math.round(plainText(md).split(" ").filter(Boolean).length / 220));
}

export { esc as escapeHtml };
