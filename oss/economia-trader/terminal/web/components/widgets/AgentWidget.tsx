"use client";

// economia-trader bridge (network-agents-setup addition): what the trading agent is doing, next to the
// market. Read-only, from GET /api/agent (state.json + journal.jsonl + alerts.jsonl of the agent).
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/api";
import { useTerminal } from "../../store/terminal";
import { terminalSymbol } from "../../lib/symbol";

type AgentEvent = { ts: string; kind: string; text: string };
type AgentSnapshot =
  | { configured: false; reason: string }
  | {
      configured: true;
      mode: string | null;
      exchange: string | null;
      configVersion: string | null;
      killSwitch: boolean;
      cash: string | null;
      realizedToday: string | null;
      errorsInRow: number;
      positions: Array<{ symbol: string; qty: string; avgPrice: string | null; stop: string | null; stopOnExchange: boolean }>;
      pendingOrders: number;
      grid: { lower: string | null; upper: string | null; lots: number } | null;
      lastTick: { at: string; ageSeconds: number; stale: boolean } | null;
      events: AgentEvent[];
      alerts: AgentEvent[];
    };

const ALARM = new Set(["auto_kill", "error", "run_error", "reconcile_mismatch", "stop_client_side", "stop_dropped", "grid_refused", "blocked"]);

function age(s: number): string {
  if (s < 90) return `${s}s`;
  if (s < 5400) return `${Math.round(s / 60)} min`;
  return `${(s / 3600).toFixed(1)} h`;
}

const hhmm = (ts: string) => (ts ? ts.slice(11, 19) : "");

/** Decimal strings from the agent (exact, many digits) shown rounded; "—" when absent. */
function num(v: string | null | undefined, digits = 2): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = Number(v);
  return Number.isFinite(n) ? n.toLocaleString("en-US", { maximumFractionDigits: digits }) : v;
}

export default function AgentWidget() {
  const setActiveSymbol = useTerminal((s) => s.setActiveSymbol);
  const { data, error } = useQuery({
    queryKey: ["agent"],
    queryFn: () => apiGet<AgentSnapshot>("/api/agent"),
    refetchInterval: 5_000,
  });

  if (error) return <div className="p-2 down">Error: {(error as Error).message}</div>;
  if (!data) return <div className="p-2 dim">Loading agent state…</div>;
  if (!data.configured) {
    return (
      <div className="p-2 text-[11px]">
        <div className="amber">Agent not connected</div>
        <div className="dim mt-1">{data.reason}</div>
        <div className="dim mt-1">e.g. ECONOMIA_TRADER_STATE_DIR=~/et-paper npm run dev</div>
      </div>
    );
  }

  const tick = data.lastTick;
  return (
    <div className="text-[11px]">
      <div className="flex flex-wrap gap-2 px-2 py-1 border-b border-[var(--border)]">
        <span className={data.mode === "paper" ? "up" : "amber"}>{(data.mode ?? "?").toUpperCase()}</span>
        <span className="dim">{data.exchange ?? "?"}</span>
        <span className="dim">v{data.configVersion ?? "?"}</span>
        <span className={data.killSwitch ? "down font-bold" : "dim"}>{data.killSwitch ? "KILL SWITCH ON" : "kill: off"}</span>
        <span className={!tick || tick.stale ? "down font-bold" : "dim"}>
          {!tick ? "NO TICK YET" : tick.stale ? `STALE · last tick ${age(tick.ageSeconds)} ago` : `tick ${age(tick.ageSeconds)} ago`}
        </span>
        {data.errorsInRow > 0 && <span className="down">errors in a row: {data.errorsInRow}</span>}
      </div>
      <div className="flex gap-3 px-2 py-1 dim">
        <span>cash {num(data.cash)}</span>
        <span>realized today {num(data.realizedToday)}</span>
        <span>pending orders {data.pendingOrders}</span>
        {data.grid && (
          <span>
            grid {num(data.grid.lower)}–{num(data.grid.upper)} · lots {data.grid.lots}
          </span>
        )}
      </div>

      <table className="data-table">
        <thead>
          <tr><th>Position</th><th>Qty</th><th>Avg</th><th>Stop</th><th>Where</th></tr>
        </thead>
        <tbody>
          {data.positions.length === 0 && (
            <tr><td className="dim" colSpan={5}>flat</td></tr>
          )}
          {data.positions.map((p) => (
            <tr key={p.symbol} className="cursor-pointer" onClick={() => setActiveSymbol(terminalSymbol(p.symbol) ?? p.symbol)}>
              <td className="font-bold">{p.symbol}</td>
              <td>{num(p.qty, 8)}</td>
              <td>{num(p.avgPrice)}</td>
              <td>{num(p.stop)}</td>
              <td className={p.stopOnExchange ? "up" : "amber"}>{p.stop ? (p.stopOnExchange ? "exchange" : "client") : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {data.alerts.length > 0 && (
        <div className="px-2 pt-2">
          <div className="dim uppercase text-[10px]">Alerts</div>
          {data.alerts.slice(0, 3).map((a, i) => (
            <div key={`${a.ts}-${i}`} className="down truncate" title={a.text}>
              {hhmm(a.ts)} {a.text}
            </div>
          ))}
        </div>
      )}

      <div className="px-2 pt-2 pb-1">
        <div className="dim uppercase text-[10px]">Decisions (newest first)</div>
        {data.events.map((e, i) => (
          <div key={`${e.ts}-${i}`} className={`truncate ${ALARM.has(e.kind) ? "down" : e.kind === "fill" ? "up" : ""}`} title={e.text}>
            <span className="dim">{hhmm(e.ts)} </span>
            {e.text}
          </div>
        ))}
      </div>
      <div className="px-2 pb-1 dim text-[10px]">Read-only view of the economia-trader state dir. The terminal never places orders.</div>
    </div>
  );
}
