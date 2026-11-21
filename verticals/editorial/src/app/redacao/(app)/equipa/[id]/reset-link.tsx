"use client";
import { useActionState, useState } from "react";
import { createResetLinkAction, type ResetLinkState } from "../../../actions";

/** Gera o link de recuperação e mostra-o UMA vez, para a direção o entregar por um canal seguro. */
export function ResetLink({ userId, name }: { userId: string; name: string }) {
  const [state, action, pending] = useActionState<ResetLinkState, FormData>(createResetLinkAction, {});
  const [copied, setCopied] = useState(false);
  return (
    <div className="stack">
      <form action={action}>
        <input type="hidden" name="user" value={userId} />
        <button className="btn" type="submit" disabled={pending}>{pending ? "A gerar…" : "Gerar link de recuperação"}</button>
      </form>
      {state.error && <p className="flash erro" style={{ margin: 0 }}>{state.error}</p>}
      {state.link && (
        <div className="notice-box">
          <b>Link para {name}</b> (uso único, válido até {new Date(state.expires!).toLocaleString("pt-PT", { timeZone: "Europe/Lisbon" })}):
          <div className="row" style={{ marginTop: 8 }}>
            <input readOnly value={state.link} aria-label="Link de recuperação" onFocus={(e) => e.currentTarget.select()} style={{ flex: "1 1 260px" }} />
            <button type="button" className="btn small" onClick={async () => { await navigator.clipboard?.writeText(state.link!); setCopied(true); }}>{copied ? "Copiado" : "Copiar"}</button>
          </div>
          <small className="muted">Envia-o só por um canal privado. Gerar outro anula este.</small>
        </div>
      )}
    </div>
  );
}
