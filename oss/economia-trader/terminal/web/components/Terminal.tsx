"use client";

import { useEffect } from "react";
import TopBar from "./TopBar";
import Sidebar from "./Sidebar";
import Workspace from "./Workspace";
import CommandPalette from "./CommandPalette";
import { useTerminal } from "../store/terminal";
import { terminalSymbol } from "../lib/symbol";

export default function Terminal() {
  const setCommandOpen = useTerminal((s) => s.setCommandOpen);
  const addWidget = useTerminal((s) => s.addWidget);
  const setActiveSymbol = useTerminal((s) => s.setActiveSymbol);

  // Deep link (network-agents-setup): /?symbol=AAPL opens that symbol, so the economia-trader dashboard
  // can link each ticker here. setActiveSymbol normalises and rejects anything that is not a symbol.
  useEffect(() => {
    const sym = new URLSearchParams(window.location.search).get("symbol");
    const target = sym ? terminalSymbol(sym) : null;
    if (target) setActiveSymbol(target);
  }, [setActiveSymbol]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandOpen(true);
        return;
      }
      if (e.altKey) {
        const map: Record<string, () => void> = {
          "1": () => addWidget("chart"),
          "2": () => addWidget("quote"),
          "3": () => addWidget("news"),
          "4": () => addWidget("screener"),
          "5": () => addWidget("heatmap"),
          "6": () => addWidget("crypto"),
          "7": () => addWidget("options"),
          "8": () => addWidget("portfolio"),
          "9": () => addWidget("ai"),
          "0": () => addWidget("agent"),
        };
        const fn = Object.hasOwn(map, e.key) ? map[e.key] : undefined; // only our own keys, never "constructor" etc.
        if (fn) {
          e.preventDefault();
          fn();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setCommandOpen, addWidget]);

  return (
    <div className="flex flex-col h-screen">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Workspace />
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
