"use client";
import { diffWords } from "diff";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

/**
 * Editor do artigo (D2 + D4).
 * - Markdown com barra de formatação e o dialecto do site (figuras com legenda e crédito, vídeos).
 * - Autosave no SERVIDOR (rascunho, sem criar versões): 2 s depois de parar de escrever, no máximo a cada 30 s,
 *   e ao sair da página (keepalive). O browser só guarda uma cópia enquanto o servidor não confirma.
 * - Conflitos: se outra pessoa gravou o rascunho entretanto, nada é sobreposto sem decisão explícita.
 * - «Guardar versão» envia o formulário (acção do servidor), que recusa se a peça mudou desde a versão de base.
 */

export type Fields = {
  title: string; subtitle: string; summary: string; body: string; slug: string | null; hero_image_url: string | null;
  hero_caption: string; hero_credit: string; tags: string[]; seo_title: string; meta_description: string; kind: string;
};
export interface DraftInfo {
  rev: number; base_version: number; fields: Fields; updated_by: string | null; updated_at: string; by_name: string | null;
  lease_user: string | null; lease_until: string | null; lease_name: string | null;
}
interface Props {
  storyId: string; version: number; state: string; editable: boolean; me: string; saved: Fields; draft: DraftInfo | null;
  photos: { url: string; title: string; credit: string }[];
  action: (form: FormData) => void | Promise<void>;
}

type Status = { kind: "idle" | "saving" | "saved" | "offline" | "conflict" | "error"; text: string };
/** Como o servidor normaliza (parseArticle): sem isto, «igual» falhava por espaços, maiúsculas nas etiquetas ou slug vazio. */
const norm = (f: Fields) => ({
  ...f, title: f.title.trim(), subtitle: f.subtitle.trim(), summary: f.summary.trim(), slug: f.slug?.trim() || null,
  hero_image_url: f.hero_image_url?.trim() || null, hero_caption: f.hero_caption.trim(), hero_credit: f.hero_credit.trim(),
  seo_title: f.seo_title.trim(), meta_description: f.meta_description.trim(),
  tags: f.tags.map((t) => t.trim().toLowerCase()).filter(Boolean),
});
const same = (a: Fields, b: Fields) => JSON.stringify(norm(a)) === JSON.stringify(norm(b));
// os browsers recusam pedidos keepalive com corpo acima de 64 KB: acima disso fica a cópia local
const KEEPALIVE_MAX = 60_000;
const hhmm = (d: string | Date) => new Date(d).toLocaleTimeString("pt-PT", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Lisbon" });
const store = {
  get(k: string) { try { return JSON.parse(localStorage.getItem(k) ?? "null"); } catch { return null; } },
  set(k: string, v: unknown) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* sem armazenamento: o servidor é a fonte */ } },
  del(k: string) { try { localStorage.removeItem(k); } catch { /* idem */ } },
};

export function ArticleEditor({ storyId, version, state, editable, me, saved, draft, photos, action }: Props) {
  const mine = draft && draft.updated_by === me;
  const [fields, setFields] = useState<Fields>(mine ? draft.fields : saved);
  const [rev, setRev] = useState<number | null>(mine ? draft.rev : null);
  const [base, setBase] = useState<number>(mine ? draft.base_version : version);
  const [server, setServer] = useState<Fields>(mine ? draft.fields : saved); // último conteúdo confirmado pelo servidor
  const [status, setStatus] = useState<Status>(mine ? { kind: "saved", text: `Rascunho recuperado (gravado às ${hhmm(draft.updated_at)})` } : { kind: "idle", text: "" });
  const [conflict, setConflict] = useState<DraftInfo | null>(null);
  const [staleVersion, setStaleVersion] = useState<number | null>(mine && draft.base_version !== version ? version : null);
  const [localBuffer, setLocalBuffer] = useState<{ fields: Fields; at: string; base: number } | null>(null);
  const [preview, setPreview] = useState(false);
  const [html, setHtml] = useState("");
  const body = useRef<HTMLTextAreaElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const firstDirty = useRef<number | null>(null);
  const live = useRef({ fields, rev, base, server });
  live.current = { fields, rev, base, server };
  const key = `ed-draft:${storyId}`;
  const other = draft && !mine ? draft : null;
  const leaseOther = other && other.lease_user && other.lease_until && new Date(other.lease_until) > new Date() ? other : null;

  // cópia local deixada por uma sessão anterior que o servidor nunca confirmou
  useEffect(() => {
    const b = store.get(key) as { fields: Fields; at: string; base: number } | null;
    if (!b) return;
    if (same(b.fields, mine ? draft.fields : saved) || same(b.fields, saved)) { store.del(key); return; }
    setLocalBuffer(b);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const send = useCallback(async (force = false, leaving = false) => {
    const { fields: f, rev: r, base: b, server: srv } = live.current;
    if (!editable || (same(f, srv) && !force)) return;
    setStatus({ kind: "saving", text: "A guardar no servidor…" });
    const body = JSON.stringify({ rev: r, baseVersion: b, fields: f, force });
    try {
      const res = await fetch(`/redacao/rascunho/${storyId}`, {
        method: "POST", headers: { "content-type": "application/json" },
        keepalive: leaving && new TextEncoder().encode(body).length < KEEPALIVE_MAX, // bytes, não caracteres
        body,
      });
      const j = await res.json().catch(() => ({}));
      if (res.status === 200) {
        setRev(j.rev); setServer(f); store.del(key); firstDirty.current = null;
        setStatus({ kind: "saved", text: `Rascunho guardado no servidor às ${hhmm(j.updated_at)}` });
        setConflict(null);
      } else if (res.status === 409) {
        if (j.reason === "version") setStaleVersion(j.version);
        if (j.draft && j.draft.updated_by !== me) setConflict(j.draft);
        else if (j.draft) { setRev(j.draft.rev); }
        setStatus({ kind: "conflict", text: j.reason === "version" ? `A peça já vai na versão ${j.version}` : "Outra pessoa gravou o rascunho" });
      } else {
        setStatus({ kind: "error", text: j.error ?? "Não foi possível guardar o rascunho" });
      }
    } catch {
      setStatus({ kind: "offline", text: "Sem ligação: o texto está guardado só neste browser até voltar a ligação" });
    }
  }, [editable, storyId, key, me]);

  const change = (patch: Partial<Fields>) => {
    setFields((f) => {
      const next = { ...f, ...patch };
      store.set(key, { fields: next, at: new Date().toISOString(), base: live.current.base });
      return next;
    });
    setStatus((s) => (s.kind === "conflict" ? s : { kind: "idle", text: "Alterações por guardar…" }));
    firstDirty.current ??= Date.now();
    clearTimeout(timer.current);
    const waited = Date.now() - firstDirty.current;
    timer.current = setTimeout(() => void send(), waited > 30_000 ? 0 : 2_000);
  };

  // ao sair (fechar o separador, mudar de app no telemóvel), envia o que falta
  useEffect(() => {
    const flush = () => { if (document.visibilityState === "hidden" && !same(live.current.fields, live.current.server)) void send(false, true); };
    document.addEventListener("visibilitychange", flush);
    window.addEventListener("pagehide", flush);
    return () => { document.removeEventListener("visibilitychange", flush); window.removeEventListener("pagehide", flush); };
  }, [send]);

  // pré-visualização ao vivo, com o mesmo HTML do site (renderizado no servidor)
  useEffect(() => {
    if (!preview) return;
    const t = setTimeout(async () => {
      const r = await fetch("/redacao/pre-visualizar", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ body: fields.body }) }).catch(() => null);
      if (r?.ok) setHtml((await r.json()).html);
    }, 500);
    return () => clearTimeout(t);
  }, [preview, fields.body]);

  const dirty = !same(fields, server);
  const words = useMemo(() => fields.body.trim().split(/\s+/).filter(Boolean).length, [fields.body]);

  // ------------------------------------------------------------ barra de formatação
  const wrap = (before: string, after = before, placeholder = "texto") => {
    const el = body.current; if (!el) return;
    const { selectionStart: a, selectionEnd: b, value } = el;
    const sel = value.slice(a, b) || placeholder;
    const next = value.slice(0, a) + before + sel + after + value.slice(b);
    change({ body: next });
    requestAnimationFrame(() => { el.focus(); el.setSelectionRange(a + before.length, a + before.length + sel.length); });
  };
  const block = (text: string) => {
    const el = body.current; if (!el) return;
    const { selectionStart: a, value } = el;
    const lineStart = value.lastIndexOf("\n", a - 1) + 1;
    const pre = lineStart === a && (a === 0 || value[a - 1] === "\n") ? "" : "\n\n";
    const next = value.slice(0, a) + pre + text + "\n\n" + value.slice(a);
    change({ body: next });
    requestAnimationFrame(() => { el.focus(); const p = a + pre.length + text.length; el.setSelectionRange(p, p); });
  };
  const prefix = (p: string) => {
    const el = body.current; if (!el) return;
    const { selectionStart: a, selectionEnd: b, value } = el;
    const s = value.lastIndexOf("\n", a - 1) + 1;
    const lines = value.slice(s, b).split("\n").map((l) => p + l.replace(/^(#{2,3} |> |- )/, "")).join("\n");
    change({ body: value.slice(0, s) + lines + value.slice(b) });
    requestAnimationFrame(() => el.focus());
  };
  const [fig, setFig] = useState({ url: "", caption: "", credit: "" });
  const insertFigure = () => {
    if (!/^https?:\/\//.test(fig.url)) return;
    const esc = (s: string) => s.replace(/[[\]"]/g, "");
    block(`![${esc(fig.caption)}](${fig.url}${fig.credit ? ` "${esc(fig.credit)}"` : ""})`);
    setFig({ url: "", caption: "", credit: "" });
  };
  const keys = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    if (e.key === "b") { e.preventDefault(); wrap("**"); }
    if (e.key === "i") { e.preventDefault(); wrap("*"); }
    if (e.key === "s") { e.preventDefault(); void send(); }
  };

  return (
    <div className="stack">
      {leaseOther && <p className="flash erro" style={{ margin: 0 }}>{leaseOther.lease_name ?? "Outra pessoa"} está a editar esta peça (último registo às {hhmm(leaseOther.updated_at)}). Combina com ela antes de mexer no texto.</p>}
      {other && !conflict && (
        <div className="notice-box">
          <b>{other.by_name ?? "Outra pessoa"} tem um rascunho por guardar</b> (gravado às {hhmm(other.updated_at)}). Estás a ver a versão {version} guardada.
          <div className="row" style={{ marginTop: 8 }}>
            <button type="button" className="btn small" onClick={() => { setFields(other.fields); setServer(other.fields); setRev(other.rev); setBase(other.base_version); }}>Continuar o rascunho de {other.by_name ?? "outra pessoa"}</button>
            <a className="btn small" href={`/redacao/pre-visualizar/${storyId}`} target="_blank" rel="noreferrer">Pré-visualizar o rascunho</a>
          </div>
        </div>
      )}
      {localBuffer && (
        <div className="notice-box">
          <b>Há texto deste browser que o servidor nunca recebeu</b> ({hhmm(localBuffer.at)}{localBuffer.base !== version ? `, escrito sobre a versão ${localBuffer.base}` : ""}).
          <div className="row" style={{ marginTop: 8 }}>
            <button type="button" className="btn small primary" onClick={() => { if (localBuffer.base !== base) { setBase(localBuffer.base); live.current.base = localBuffer.base; } change(localBuffer.fields); setLocalBuffer(null); }}>Recuperar esse texto</button>
            <button type="button" className="btn small" onClick={() => { store.del(key); setLocalBuffer(null); }}>Descartar</button>
          </div>
        </div>
      )}
      {staleVersion !== null && (
        <div className="notice-box warn">
          <b>A peça já vai na versão {staleVersion}</b>; este texto foi começado na versão {base}. Guardar agora seria gravar por cima do trabalho de outra pessoa.
          <div className="row" style={{ marginTop: 8 }}>
            <a className="btn small" href={`/redacao/pecas/${storyId}/versoes?a=${base}&b=${staleVersion}`}>Ver o que mudou</a>
            <button type="button" className="btn small" onClick={async () => { await fetch(`/redacao/rascunho/${storyId}`, { method: "DELETE" }); store.del(key); location.reload(); }}>Descartar o meu rascunho e abrir a versão {staleVersion}</button>
          </div>
        </div>
      )}
      {conflict && (
        <div className="notice-box warn" role="alert">
          <b>{conflict.by_name ?? "Outra pessoa"} gravou este rascunho às {hhmm(conflict.updated_at)}</b> enquanto escrevias. Nada foi sobreposto.
          <details style={{ marginTop: 6 }}><summary>Ver diferenças no texto (o dela → o teu)</summary>
            <div className="diff">{diffWords(conflict.fields.body, fields.body).map((p, i) => p.added ? <ins key={i}>{p.value}</ins> : p.removed ? <del key={i}>{p.value}</del> : <span key={i}>{p.value}</span>)}</div>
          </details>
          <div className="row" style={{ marginTop: 8 }}>
            <button type="button" className="btn small" onClick={() => { setFields(conflict.fields); setServer(conflict.fields); setRev(conflict.rev); setBase(conflict.base_version); setConflict(null); setStatus({ kind: "saved", text: "Carregado o rascunho dela" }); }}>Ficar com o texto dela</button>
            <button type="button" className="btn small primary" onClick={() => { setRev(conflict.rev); live.current.rev = conflict.rev; void send(true); }}>Ficar com o meu (sobrepõe o dela)</button>
          </div>
        </div>
      )}

      <form action={action} className="stack" onSubmit={() => {
        clearTimeout(timer.current);
        // cópia local antes de enviar: se a gravação for recusada (versão nova de outra pessoa), o texto recupera-se
        store.set(key, { fields: live.current.fields, at: new Date().toISOString(), base: live.current.base });
      }}>
        <input type="hidden" name="id" value={storyId} />
        <input type="hidden" name="base_version" value={base} />
        <input type="hidden" name="tags" value={fields.tags.join(", ")} />
        <fieldset disabled={!editable} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }} className="stack">
          <label className="field"><span>Título</span><input id="a-title" name="title" value={fields.title} onChange={(e) => change({ title: e.target.value })} required maxLength={300} /></label>
          <label className="field"><span>Subtítulo</span><input id="a-subtitle" name="subtitle" value={fields.subtitle} onChange={(e) => change({ subtitle: e.target.value })} maxLength={600} /></label>
          <label className="field"><span>Resumo</span><textarea id="a-summary" name="summary" value={fields.summary} onChange={(e) => change({ summary: e.target.value })} style={{ minHeight: 70 }} /><small>Aparece na página inicial e nas partilhas.</small></label>

          <div className="field">
            <span id="a-body-label">Texto</span>
            {editable && (
              <div className="toolbar" role="toolbar" aria-label="Formatação do texto">
                <button type="button" title="Negrito (Ctrl+B)" onClick={() => wrap("**")}><b>N</b></button>
                <button type="button" title="Itálico (Ctrl+I)" onClick={() => wrap("*")}><i>I</i></button>
                <button type="button" title="Intertítulo" onClick={() => prefix("## ")}>Intertítulo</button>
                <button type="button" title="Subintertítulo" onClick={() => prefix("### ")}>Sub</button>
                <button type="button" title="Citação" onClick={() => prefix("> ")}>« »</button>
                <button type="button" title="Lista" onClick={() => prefix("- ")}>Lista</button>
                <button type="button" title="Ligação" onClick={() => wrap("[", "](https://)", "texto da ligação")}>Ligação</button>
                <button type="button" title="Separador" onClick={() => block("---")}>—</button>
                <details className="toolbar-pop"><summary>Imagem</summary>
                  <div className="stack pop">
                    {photos.length > 0 && <label className="field"><span>Das referências</span>
                      <select value="" onChange={(e) => { const p = photos[Number(e.target.value)]; if (p) setFig({ url: p.url, caption: p.title, credit: p.credit }); }}>
                        <option value="">Escolher fotografia…</option>{photos.map((p, i) => <option key={p.url} value={i}>{p.title || p.url}</option>)}</select></label>}
                    <label className="field"><span>Endereço (https://)</span><input value={fig.url} onChange={(e) => setFig({ ...fig, url: e.target.value })} /></label>
                    <label className="field"><span>Legenda</span><input value={fig.caption} onChange={(e) => setFig({ ...fig, caption: e.target.value })} /></label>
                    <label className="field"><span>Crédito</span><input value={fig.credit} onChange={(e) => setFig({ ...fig, credit: e.target.value })} /></label>
                    <button type="button" className="btn small primary" disabled={!/^https?:\/\//.test(fig.url)} onClick={insertFigure}>Inserir figura</button>
                  </div>
                </details>
                <button type="button" title="Vídeo do YouTube ou Vimeo: cola o endereço sozinho numa linha" onClick={() => block("https://www.youtube.com/watch?v=")}>Vídeo</button>
                <label className="check" style={{ marginLeft: "auto" }}><input type="checkbox" checked={preview} onChange={(e) => setPreview(e.target.checked)} /> Pré-visualizar ao lado</label>
              </div>
            )}
            <div className={preview ? "editor-split" : ""}>
              <textarea id="a-body" ref={body} className="body" name="body" aria-labelledby="a-body-label" value={fields.body}
                onChange={(e) => change({ body: e.target.value })} onKeyDown={keys} />
              {preview && <div className="article preview-live" aria-label="Pré-visualização" dangerouslySetInnerHTML={{ __html: html }} />}
            </div>
            <small>{words} palavras · {Math.max(1, Math.round(words / 220))} min de leitura · Markdown: ## intertítulo, **negrito**, *itálico*, &gt; citação. Imagem sozinha numa linha vira figura com legenda e crédito.</small>
          </div>

          <div className="grid2">
            <label className="field"><span>Tipo</span>
              <select id="a-kind" name="kind" value={fields.kind} onChange={(e) => change({ kind: e.target.value })}><option value="news">Notícia ou reportagem</option><option value="opinion">Opinião</option>
                <option value="interview">Entrevista</option><option value="sponsored">Conteúdo patrocinado</option></select></label>
            <label className="field"><span>Endereço (URL)</span><input id="a-slug" name="slug" value={fields.slug ?? ""} onChange={(e) => change({ slug: e.target.value })} placeholder="gerado a partir do título" /></label>
            <label className="field"><span>Etiquetas</span><input id="a-tags" value={fields.tags.join(", ")} onChange={(e) => change({ tags: e.target.value.split(",").map((t) => t.trimStart()) })} placeholder="separadas por vírgulas" /></label>
          </div>
          <details className="box" open={!!fields.hero_image_url}><summary>Imagem principal</summary>
            <div className="hero-edit" style={{ marginTop: 10 }}>
              <div className="stack">
                <label className="field"><span>Endereço da imagem</span><input id="a-hero" name="hero_image_url" type="url" value={fields.hero_image_url ?? ""} onChange={(e) => change({ hero_image_url: e.target.value || null })} placeholder="https://…" /></label>
                {photos.length > 0 && <label className="field"><span>Ou escolhe das referências</span>
                  <select value="" onChange={(e) => { const p = photos[Number(e.target.value)]; if (p) change({ hero_image_url: p.url, hero_caption: fields.hero_caption || p.title, hero_credit: p.credit || fields.hero_credit }); }}>
                    <option value="">Escolher fotografia…</option>{photos.map((p, i) => <option key={p.url} value={i}>{p.title || p.url}</option>)}</select></label>}
                <div className="grid2">
                  <label className="field"><span>Legenda</span><input id="a-caption" name="hero_caption" value={fields.hero_caption} onChange={(e) => change({ hero_caption: e.target.value })} /></label>
                  <label className="field"><span>Crédito</span><input id="a-credit" name="hero_credit" value={fields.hero_credit} onChange={(e) => change({ hero_credit: e.target.value })} /></label>
                </div>
                {fields.hero_image_url && !fields.hero_credit && <small className="warn-text">Falta o crédito da imagem.</small>}
              </div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {fields.hero_image_url && /^https?:\/\//.test(fields.hero_image_url) && <img className="hero-thumb" src={fields.hero_image_url} alt="" />}
            </div>
          </details>
          <details className="box"><summary>Pesquisa (SEO)</summary>
            <div className="stack" style={{ marginTop: 10 }}>
              <label className="field"><span>Título para pesquisa <span className="muted">({fields.seo_title.length}/60)</span></span><input id="a-seo" name="seo_title" value={fields.seo_title} onChange={(e) => change({ seo_title: e.target.value })} maxLength={120} /><small>Vazio usa o título.</small></label>
              <label className="field"><span>Descrição <span className="muted">({fields.meta_description.length}/155)</span></span><textarea id="a-meta" name="meta_description" value={fields.meta_description} onChange={(e) => change({ meta_description: e.target.value })} style={{ minHeight: 60 }} maxLength={320} /><small>Vazio usa o resumo.</small></label>
            </div>
          </details>
          {state === "published"
            ? <label className="field"><span>Nota da alteração (obrigatória)</span><input id="a-note" name="note" required placeholder="O que mudou no artigo publicado e porquê" maxLength={300} /><small>A alteração conta como nova aprovação tua e fica no histórico.</small></label>
            : <label className="field"><span>Nota desta versão</span><input id="a-note" name="note" placeholder="Ex.: acrescentei a reação da câmara" maxLength={300} /></label>}
          {editable && (
            <div className="row save-bar">
              <button className="btn primary" type="submit">Guardar versão</button>
              <a className="btn" href={`/redacao/pre-visualizar/${storyId}`} target="_blank" rel="noreferrer">Ver como no site</a>
              <span className={`autosave ${status.kind}`} role="status" aria-live="polite">{status.text || (dirty ? "Alterações por guardar…" : "Sem alterações por guardar")}</span>
            </div>
          )}
        </fieldset>
      </form>
    </div>
  );
}
