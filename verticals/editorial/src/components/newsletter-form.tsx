import { subscribeAction } from "@/app/(site)/actions";
import { CONSENT_TEXT } from "@/lib/newsletter";

const MSG: Record<string, [string, string]> = {
  ok: ["ok", "Inscrição feita. Obrigado!"],
  consent: ["erro", "Para te inscreveres, aceita receber a newsletter."],
  email: ["erro", "Esse email não parece válido."],
};

/** Formulário de inscrição (funciona sem JavaScript). O texto do consentimento é guardado tal como é mostrado. */
export function NewsletterForm({ pubName, status, where = "rodape" }: { pubName: string; status?: string; where?: "rodape" | "pagina" }) {
  const id = (x: string) => (where === "rodape" ? x : `${x}-${where}`); // identificadores únicos na mesma página
  const consent = CONSENT_TEXT(pubName);
  const m = status ? MSG[status] : undefined;
  return (
    <form action={subscribeAction} className="newsletter" id={id("newsletter")}>
      <b>Newsletter</b>
      <input type="hidden" name="consent_text" value={consent} />
      <div className="hp" aria-hidden="true"><label>Website <input name="website" tabIndex={-1} autoComplete="off" /></label></div>
      <div className="row">
        <label className="sr-only" htmlFor={id("nl-email")}>Email</label>
        <input id={id("nl-email")} name="email" type="email" required placeholder="o-teu@email.pt" autoComplete="email" style={{ flex: "1 1 180px" }} />
        <button className="btn small" type="submit">Inscrever</button>
      </div>
      <label className="check" style={{ fontSize: 13 }}><input type="checkbox" name="consent" value="1" required /> {consent}</label>
      {m && <p className={`flash ${m[0]}`} role="status" style={{ margin: 0 }}>{m[1]}</p>}
    </form>
  );
}
