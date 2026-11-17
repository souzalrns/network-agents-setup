import { marked } from "marked";
import sanitizeHtml from "sanitize-html";

marked.setOptions({ gfm: true, breaks: false });

/** Texto do artigo (Markdown) para HTML seguro: só etiquetas de texto, ligações e imagens http(s). */
export function renderMarkdown(md: string): string {
  const raw = marked.parse(md ?? "", { async: false }) as string;
  return sanitizeHtml(raw, {
    allowedTags: ["p", "h2", "h3", "h4", "blockquote", "ul", "ol", "li", "strong", "em", "a", "br", "hr",
      "figure", "figcaption", "img", "code", "pre", "table", "thead", "tbody", "tr", "th", "td", "sup", "sub"],
    allowedAttributes: { a: ["href", "title", "rel", "target"], img: ["src", "alt", "title", "width", "height", "loading"] },
    allowedSchemes: ["http", "https", "mailto"],
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
