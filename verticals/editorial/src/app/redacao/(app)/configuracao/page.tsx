import { Flash } from "@/components/ui";
import { requireLead } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { AGENT_FALLBACK_NAMES, getPublication } from "@/lib/publication";
import { listSections } from "@/lib/queries";
import { savePageAction, savePublicationAction, saveSectionAction } from "../../actions";

const SOCIAL = ["instagram", "youtube", "podcast", "tiktok", "x", "facebook", "linkedin", "newsletter"];
const LEGAL: [string, string][] = [["owner", "Proprietário"], ["director", "Diretor(a)"], ["registration", "Registo na ERC"],
  ["nipc", "NIPC"], ["address", "Sede da redação"], ["statute_url", "Estatuto editorial (endereço)"]];
const PAGES: [string, string][] = [["sobre", "Sobre"], ["contactos", "Contactos"], ["estatuto-editorial", "Estatuto editorial"],
  ["politica-de-correcoes", "Política de correções"], ["privacidade", "Política de privacidade"]];

export default async function Configuracao({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { ctx } = await requireLead();
  const sp = await searchParams;
  const pub = await getPublication(ctx);
  const { sections, pages } = await withCtx(ctx, async (tx) => ({
    sections: await listSections(tx),
    pages: await tx<{ slug: string; title: string; body: string; published: boolean }[]>`select slug, title, body, published from pages order by slug`,
  }));
  return (
    <>
      <div className="nr-head"><div><p className="label">Direção</p><h1>Configuração da publicação</h1></div></div>
      <Flash sp={sp} />
      <p className="muted" style={{ marginTop: 0, maxWidth: "75ch" }}>A identidade da publicação vive aqui, não no código: mudar o nome, as cores ou o domínio muda o site e a redação sem tocar em nada mais.</p>
      <form action={savePublicationAction} className="stack">
        <section className="card stack">
          <h2>Identidade</h2>
          <div className="grid2">
            <label className="field"><span>Nome</span><input id="c-name" name="name" defaultValue={pub.name} required /></label>
            <label className="field"><span>Assinatura</span><input id="c-tagline" name="tagline" defaultValue={pub.tagline} /></label>
            <label className="field"><span>Cor principal</span><input id="c-primary" name="primary_color" type="color" defaultValue={pub.primary_color} /></label>
            <label className="field"><span>Cor de destaque</span><input id="c-secondary" name="secondary_color" type="color" defaultValue={pub.secondary_color} /></label>
            <label className="field"><span>Logótipo (endereço)</span><input id="c-logo" name="logo_url" type="url" defaultValue={pub.logo_url ?? ""} /></label>
            <label className="field"><span>Ícone (endereço)</span><input id="c-fav" name="favicon_url" type="url" defaultValue={pub.favicon_url ?? ""} /></label>
            <label className="field"><span>Domínio</span><input id="c-domain" name="domain" defaultValue={pub.domain ?? ""} placeholder="exemplo.pt" /></label>
            <label className="field"><span>Língua</span><input id="c-lang" name="language" defaultValue={pub.language} /></label>
          </div>
          <label className="field"><span>Descrição</span><textarea id="c-desc" name="description" defaultValue={pub.description} style={{ minHeight: 70 }} /></label>
        </section>
        <section className="card stack">
          <h2>Contactos e redes</h2>
          <div className="grid2">
            <label className="field"><span>Email da redação</span><input id="c-email" name="contact_email" type="email" defaultValue={pub.contact_email ?? ""} /></label>
            <label className="field"><span>Morada</span><input id="c-addr" name="contact_address" defaultValue={pub.contact_address ?? ""} /></label>
            {SOCIAL.map((k) => <label key={k} className="field"><span>{k}</span><input name={`social_${k}`} type="url" defaultValue={pub.social_links?.[k] ?? ""} placeholder="https://…" /></label>)}
          </div>
        </section>
        <section className="card stack">
          <h2>Ficha técnica e enquadramento legal</h2>
          <p className="muted" style={{ margin: 0 }}>Aparece no rodapé do site. Uma publicação periódica em Portugal regista-se na ERC antes de começar a publicar.</p>
          <div className="grid2">{LEGAL.map(([k, l]) => <label key={k} className="field"><span>{l}</span><input name={`legal_${k}`} defaultValue={pub.legal?.[k] ?? ""} /></label>)}</div>
        </section>
        <section className="card stack">
          <h2>Regras e agentes</h2>
          <label className="check"><input type="checkbox" name="require_second_reviewer" value="1" defaultChecked={pub.settings?.require_second_reviewer !== false} /> Quem escreve uma peça não a pode aprovar (recomendado)</label>
          <label className="check"><input type="checkbox" name="public_launch" value="1" defaultChecked={pub.public_launch} /> Site lançado (sem esta opção o site mostra um aviso de pré-lançamento e pede aos motores de pesquisa que não indexem)</label>
          <div className="grid2">{Object.entries(AGENT_FALLBACK_NAMES).map(([id, fallback]) => (
            <label key={id} className="field"><span>Nome do agente {fallback}</span><input name={`agent_${id}`} defaultValue={pub.agent_names?.[id] ?? ""} placeholder={fallback} /><small>{id}</small></label>))}</div>
        </section>
        <div><button className="btn primary" type="submit">Guardar configuração</button></div>
      </form>

      <section className="card stack" id="editorias" style={{ marginTop: 18 }}>
        <h2>Editorias</h2>
        {sections.map((s) => (
          <form key={s.id} action={saveSectionAction} className="row">
            <input type="hidden" name="section" value={s.id} />
            <input name="name" defaultValue={s.name} aria-label="Nome" style={{ flex: "2 1 180px", width: "auto" }} />
            <input name="slug" defaultValue={s.slug} aria-label="Endereço" style={{ flex: "1 1 120px", width: "auto" }} />
            <input name="color" type="color" defaultValue={s.color} aria-label="Cor" style={{ width: 56 }} />
            <input name="position" type="number" defaultValue={s.position} aria-label="Ordem" style={{ width: 80 }} />
            <select name="active" defaultValue={s.active ? "1" : "0"} aria-label="Estado" style={{ width: "auto" }}><option value="1">Ativa</option><option value="0">Inativa</option></select>
            <input type="hidden" name="description" value={s.description} />
            <button className="btn small" type="submit">Guardar</button>
          </form>
        ))}
        <form action={saveSectionAction} className="row">
          <input name="name" placeholder="Nova editoria" aria-label="Nova editoria" required style={{ flex: "2 1 180px", width: "auto" }} />
          <input name="color" type="color" defaultValue="#7a8480" aria-label="Cor" style={{ width: 56 }} />
          <input name="position" type="number" defaultValue={sections.length + 1} aria-label="Ordem" style={{ width: 80 }} />
          <button className="btn small" type="submit">Acrescentar</button>
        </form>
      </section>

      <section className="card stack" id="paginas" style={{ marginTop: 18 }}>
        <h2>Páginas institucionais</h2>
        {PAGES.map(([slug, title]) => {
          const p = pages.find((x) => x.slug === slug);
          return (
            <details key={slug} className="box"><summary>{p?.title ?? title} {p?.published ? "" : "· por publicar"}</summary>
              <form action={savePageAction} className="stack" style={{ marginTop: 10 }}>
                <input type="hidden" name="slug" value={slug} />
                <label className="field"><span>Título</span><input name="title" defaultValue={p?.title ?? title} /></label>
                <label className="field"><span>Texto (Markdown)</span><textarea name="body" defaultValue={p?.body ?? ""} style={{ minHeight: 200 }} /></label>
                <label className="check"><input type="checkbox" name="published" value="1" defaultChecked={p?.published ?? false} /> Publicada</label>
                <div><button className="btn small" type="submit">Guardar página</button></div>
              </form>
            </details>
          );
        })}
      </section>
    </>
  );
}
