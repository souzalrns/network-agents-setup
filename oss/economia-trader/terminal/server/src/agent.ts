// economia-trader bridge (network-agents-setup addition, not upstream OpenTerminal).
//
// Read-only view of what the trading agent is doing, built from the files economia-trader already
// writes in its state dir: state.json (book, stops, pending orders), journal.jsonl (every decision,
// hash-chained) and alerts.jsonl. The terminal never writes there and never places orders: it only
// shows the agent next to the market. The state dir comes from ECONOMIA_TRADER_STATE_DIR; nothing in
// a request can choose which file is read.

import { closeSync, existsSync, fstatSync, openSync, readSync, statSync } from "node:fs";
import { join } from "node:path";

export const STATE_FILE = "state.json";
export const JOURNAL_FILE = "journal.jsonl";
export const ALERTS_FILE = "alerts.jsonl";
export const KILL_FILE = "KILL";
const TAIL_BYTES = 512 * 1024; // the journal grows forever: read only its end
const SECRETISH = /key|secret|token|password|signature|auth/i;

export type AgentPosition = {
  symbol: string;
  qty: string;
  avgPrice: string | null;
  stop: string | null;
  stopOnExchange: boolean;
};

export type AgentEvent = { ts: string; kind: string; text: string };

export type AgentSnapshot =
  | { configured: false; reason: string }
  | {
      configured: true;
      stateDir: string;
      mode: string | null;
      exchange: string | null;
      configVersion: string | null;
      killSwitch: boolean;
      cash: string | null;
      realizedToday: string | null;
      errorsInRow: number;
      positions: AgentPosition[];
      pendingOrders: number;
      grid: { lower: string | null; upper: string | null; lots: number } | null;
      lastTick: { at: string; ageSeconds: number; stale: boolean } | null;
      events: AgentEvent[];
      alerts: AgentEvent[];
      generatedAt: string;
    };

function readTail(path: string, maxBytes = TAIL_BYTES): string {
  if (!existsSync(path)) return "";
  const fd = openSync(path, "r");
  try {
    const size = fstatSync(fd).size;
    const start = Math.max(0, size - maxBytes);
    const buf = Buffer.alloc(size - start);
    readSync(fd, buf, 0, buf.length, start);
    const text = buf.toString("utf8");
    return start > 0 ? text.slice(text.indexOf("\n") + 1) : text; // drop the cut first line
  } finally {
    closeSync(fd);
  }
}

function jsonLines(text: string): Array<Record<string, unknown>> {
  const out: Array<Record<string, unknown>> = [];
  for (const line of text.split("\n")) {
    if (!line.trim()) continue;
    try {
      const v = JSON.parse(line);
      if (v && typeof v === "object") out.push(v as Record<string, unknown>);
    } catch {
      // a half-written last line (the agent is appending right now) is skipped, never fatal
    }
  }
  return out;
}

/** Drop anything that looks like a credential before it can reach the browser. */
export function redact(value: unknown, depth = 0): unknown {
  if (depth > 6) return "…";
  if (Array.isArray(value)) return value.slice(0, 50).map((v) => redact(v, depth + 1));
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[k] = SECRETISH.test(k) ? "***" : redact(v, depth + 1);
    }
    return out;
  }
  return typeof value === "string" && value.length > 300 ? `${value.slice(0, 300)}…` : value;
}

const str = (v: unknown): string => (v === undefined || v === null ? "" : String(v));

/** One human line per journal entry; unknown kinds fall back to a short JSON of the payload. */
export function summarize(kind: string, payload: Record<string, unknown>): string {
  const p = (redact(payload) ?? {}) as Record<string, unknown>;
  switch (kind) {
    case "fill":
      return `fill ${str(p.side)} ${str(p.qty)} ${str(p.symbol)} @ ${str(p.price)}${p.source === "exchange" ? " (exchange)" : ""}`;
    case "intent":
      return `intent ${str(p.side)} ${str(p.qty)} ${str(p.symbol)} (${str(p.order_type)}, ${str(p.mode)})`;
    case "order":
      return `order sent ${str(p.side)} ${str(p.qty)} ${str(p.symbol)}${p.order_id ? ` #${str(p.order_id)}` : ""}`;
    case "proposal":
      return `proposal ${str(p.side)} ${str(p.symbol)} (${str(p.proposer)})`;
    case "assessment":
      return p.approved ? "risk: approved" : `risk: rejected — ${(p.reasons as unknown[] | undefined)?.join("; ") ?? ""}`;
    case "blocked":
      return `gate blocked: ${str(p.code)}`;
    case "auto_kill":
      return `AUTO-KILL: ${str(p.reason)}`;
    case "grid_refused":
      return `grid refused: ${(p.problems as unknown[] | undefined)?.join("; ") ?? ""}`;
    case "macro_block":
      return `paused (macro): ${(p.releases as unknown[] | undefined)?.join(", ") ?? ""}`;
    case "odds_block":
      return `paused (odds): ${(p.reasons as unknown[] | undefined)?.join("; ") ?? ""}`;
    case "stop_placed":
      return `stop on exchange ${str(p.symbol)} @ ${str(p.stop)}`;
    case "stop_cancelled":
      return `stop cancelled ${str(p.symbol)} (${str(p.why)})`;
    case "stop_client_side":
      return `stop stays client-side ${str(p.symbol)}: ${str(p.why)}`;
    case "stop_dropped":
      return `stop dropped by venue ${str(p.symbol)} (${str(p.status)})`;
    case "reconcile_mismatch":
      return `book vs exchange ${str(p.symbol)}: book ${str(p.book)}, exchange ${str(p.exchange)} → ${str(p.action)}`;
    case "run":
      return `tick ${str(p.as_of).slice(0, 16)} v${str(p.version)}`;
    case "error":
    case "run_error":
      return `error: ${str(p.error)}`;
    default:
      return JSON.stringify(p).slice(0, 160);
  }
}

function events(rows: Array<Record<string, unknown>>, limit: number): AgentEvent[] {
  return rows
    .slice(-limit)
    .reverse()
    .map((e) => {
      const kind = str(e.kind);
      return { ts: str(e.ts), kind, text: summarize(kind, (e.payload as Record<string, unknown>) ?? {}) };
    });
}

export function readAgentSnapshot(
  stateDir: string | undefined,
  opts: { now?: Date; staleAfterSeconds?: number; limit?: number } = {}
): AgentSnapshot {
  if (!stateDir) {
    return { configured: false, reason: "set ECONOMIA_TRADER_STATE_DIR to the economia-trader state dir" };
  }
  if (!existsSync(stateDir) || !statSync(stateDir).isDirectory()) {
    return { configured: false, reason: `state dir not found: ${stateDir}` };
  }
  const now = opts.now ?? new Date();
  const staleAfter = opts.staleAfterSeconds ?? 900;
  const limit = opts.limit ?? 25;

  let state: Record<string, any> = {};
  try {
    state = JSON.parse(readTail(join(stateDir, STATE_FILE), 4 * 1024 * 1024) || "{}");
  } catch {
    state = {}; // being rewritten (tmp + rename makes this rare): show the journal anyway
  }
  const journal = jsonLines(readTail(join(stateDir, JOURNAL_FILE)));
  const alerts = jsonLines(readTail(join(stateDir, ALERTS_FILE), 128 * 1024));

  const stops: Record<string, string> = state.stops ?? {};
  const exchangeStops: Record<string, unknown> = state.exchange_stops ?? {};
  const positions: AgentPosition[] = Object.entries((state.positions ?? {}) as Record<string, any>).map(
    ([symbol, p]) => ({
      symbol,
      qty: str(p?.qty),
      avgPrice: p?.avg_price ?? null,
      stop: stops[symbol] ?? null,
      stopOnExchange: Boolean(exchangeStops[symbol]),
    })
  );

  const lastRun = [...journal].reverse().find((e) => e.kind === "run");
  const lastTick = lastRun
    ? (() => {
        const at = str(lastRun.ts);
        const ageSeconds = Math.max(0, Math.round((now.getTime() - new Date(at).getTime()) / 1000));
        return { at, ageSeconds, stale: ageSeconds > staleAfter };
      })()
    : null;

  const grid = state.grid
    ? {
        lower: state.grid.lower ?? null,
        upper: state.grid.upper ?? null,
        lots: Object.keys(state.grid.lots ?? {}).length,
      }
    : null;

  return {
    configured: true,
    stateDir,
    mode: state.mode ?? null,
    exchange: state.exchange ?? null,
    configVersion: state.config_version ?? null,
    killSwitch: existsSync(join(stateDir, KILL_FILE)),
    cash: state.broker?.cash ?? null,
    realizedToday: state.realized_today ?? null,
    errorsInRow: Number(state.errors_in_row ?? 0),
    positions,
    pendingOrders: Object.keys(state.pending ?? {}).length,
    grid,
    lastTick,
    events: events(journal, limit),
    alerts: alerts
      .slice(-10)
      .reverse()
      .map((a) => ({ ts: str(a.sent_at ?? a.at), kind: str(a.rule), text: `${str(a.title)}: ${str(a.detail)}` })),
    generatedAt: now.toISOString(),
  };
}
