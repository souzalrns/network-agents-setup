"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { uploadImage } from "@/components/image-upload";

/** Carregar uma ou várias imagens para a biblioteca, com legenda e crédito. */
export function Uploader() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [alt, setAlt] = useState(""), [credit, setCredit] = useState("");
  const onFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true); setMsg(null);
    try {
      for (const f of Array.from(files)) await uploadImage(f, { alt, credit });
      setMsg({ ok: true, text: files.length === 1 ? "Imagem carregada." : `${files.length} imagens carregadas.` });
      setAlt(""); setCredit("");
      router.refresh();
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="stack">
      <div className="grid2">
        <label className="field"><span>Legenda</span><input id="u-alt" value={alt} onChange={(e) => setAlt(e.target.value)} /></label>
        <label className="field"><span>Crédito</span><input id="u-credit" value={credit} onChange={(e) => setCredit(e.target.value)} placeholder="Obrigatório para usar numa peça aprovada" /></label>
      </div>
      <label className="btn primary" style={{ alignSelf: "flex-start" }}>
        {busy ? "A carregar…" : "Escolher imagens"}
        <input id="u-file" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden disabled={busy} onChange={(e) => void onFiles(e.target.files)} />
      </label>
      <small className="muted">JPEG, PNG ou WebP. As fotografias são reduzidas no teu dispositivo antes de enviar (máx. 2000 px).</small>
      {msg && <p className={`flash ${msg.ok ? "ok" : "erro"}`} style={{ margin: 0 }} role="status">{msg.text}</p>}
    </div>
  );
}
