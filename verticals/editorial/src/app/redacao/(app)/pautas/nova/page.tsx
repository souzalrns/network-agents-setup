import { Flash } from "@/components/ui";
import { requireUser } from "@/lib/auth";
import { withCtx } from "@/lib/db";
import { listSections } from "@/lib/queries";
import { createStoryAction } from "../../../actions";

import { FORMATS } from "@/lib/constants";

export default async function NovaPauta({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { ctx } = await requireUser();
  const sp = await searchParams;
  const sections = await withCtx(ctx, (tx) => listSections(tx, true));
  return (
    <>
      <div className="nr-head"><div><p className="label">Banco de pautas</p><h1>Nova pauta</h1></div></div>
      <Flash sp={sp} />
      <form action={createStoryAction} className="card stack" style={{ maxWidth: 860 }}>
        <label className="field"><span>Título de trabalho</span>
          <input id="title" name="title" required maxLength={300} placeholder="Em forma de pergunta ou hipótese a investigar" />
          <small>Uma pauta é uma hipótese, não uma conclusão.</small>
        </label>
        <div className="grid2">
          <label className="field"><span>Editoria</span>
            <select id="section_id" name="section_id" defaultValue=""><option value="">Por definir</option>{sections.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
          </label>
          <label className="field"><span>Formato</span>
            <select id="format" name="format" defaultValue="reportagem">{FORMATS.map((f) => <option key={f}>{f}</option>)}</select>
          </label>
          <label className="field"><span>Prioridade</span>
            <select id="priority" name="priority" defaultValue="2"><option value="1">Alta</option><option value="2">Normal</option><option value="3">Baixa</option></select>
          </label>
          <label className="field"><span>Prazo</span><input id="due_date" name="due_date" type="date" /></label>
        </div>
        <label className="field"><span>Ângulo de investigação</span><textarea id="angle" name="angle" placeholder="O que queremos descobrir e porquê agora" /></label>
        <label className="field"><span>A confirmar antes de avançar</span><textarea id="to_confirm" name="to_confirm" placeholder="Datas, números, factos a verificar primeiro" /></label>
        <label className="field"><span>Perguntas para entrevista</span><textarea id="interview_questions" name="interview_questions" placeholder="Uma pergunta por linha" /></label>
        <p className="muted" style={{ margin: 0, fontSize: 14 }}>As fontes (pessoas e contactos) acrescentam-se na ficha da peça e ficam protegidas: os agentes nunca as vêem.</p>
        <div className="row">
          <button className="btn primary" type="submit" name="propose" value="1">Criar e propor à edição</button>
          <button className="btn" type="submit" name="propose" value="0">Guardar como ideia</button>
        </div>
      </form>
    </>
  );
}
