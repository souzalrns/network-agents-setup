import { runAgentAction } from "./agent-actions";

/** Botões para pedir trabalho aos agentes. O resultado aparece como proposta para a equipa rever. */
export function AgentPanel({ storyId, canRun, names }: { storyId: string; canRun: boolean; names: { research: string; factcheck: string; editor: string } }) {
  if (!canRun) return <p className="muted" style={{ margin: 0 }}>O teu papel não pede trabalho aos agentes.</p>;
  const agents: [string, string, string][] = [
    ["research", names.research, "Reúne contexto, cronologia, fontes primárias a consultar e perguntas."],
    ["factcheck", names.factcheck, "Extrai números, datas e citações e regista-os como afirmações por verificar."],
    ["editor", names.editor, "Aponta problemas de clareza, títulos, linguagem e afirmações sem fonte, e propõe adaptações para redes."],
  ];
  return (
    <div className="grid2">
      {agents.map(([id, name, help]) => (
        <form key={id} action={runAgentAction} className="tile">
          <input type="hidden" name="story" value={storyId} /><input type="hidden" name="agent" value={id} />
          <b>{name}</b><span className="muted" style={{ fontSize: 13 }}>{help}</span>
          <div><button className="btn small" type="submit">Pedir</button></div>
        </form>
      ))}
    </div>
  );
}
