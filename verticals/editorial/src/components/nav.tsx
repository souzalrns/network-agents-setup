"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

type Item = { href: string; label: string };

/**
 * Navegação da redacção. No computador é uma barra; no telemóvel é um botão «Menu» que abre um <dialog>
 * nativo (D1): prende o foco, fecha com Esc e devolve o foco ao botão, sem bibliotecas.
 */
export function NewsroomNav({ items, account }: { items: Item[]; account: React.ReactNode }) {
  const path = usePathname();
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { dialog.current?.close(); }, [path]); // mudar de página fecha o menu
  const links = (inMenu: boolean) => items.map((i) => {
    const active = i.href === "/redacao" ? path === "/redacao" : path.startsWith(i.href);
    return <Link key={i.href} href={i.href} aria-current={active ? "page" : undefined}
      onClick={inMenu ? () => dialog.current?.close() : undefined}>{i.label}</Link>;
  });
  const current = items.find((i) => (i.href === "/redacao" ? path === "/redacao" : path.startsWith(i.href)));
  return (
    <>
      <nav className="nr-nav" aria-label="Redação">{links(false)}</nav>
      <div className="nr-user nr-desktop">{account}</div>
      <button type="button" className="nr-menu-btn" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}>
        <span aria-hidden="true">☰</span> {current?.label ?? "Menu"}
      </button>
      <dialog ref={dialog} className="nr-dialog" aria-label="Menu da redação"
        onClick={(e) => { if (e.target === dialog.current) dialog.current?.close(); }}>
        <div className="nr-dialog-head">
          <b>Redação</b>
          <button type="button" className="btn small" onClick={() => dialog.current?.close()} autoFocus>Fechar</button>
        </div>
        <nav aria-label="Redação (menu)">{links(true)}</nav>
        <div className="nr-dialog-account">{account}</div>
      </dialog>
    </>
  );
}
