import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { readAgentSnapshot, redact, summarize } from "./agent.js";

function stateDir(files: Record<string, string>): string {
  const dir = mkdtempSync(join(tmpdir(), "et-agent-"));
  for (const [name, body] of Object.entries(files)) writeFileSync(join(dir, name), body);
  return dir;
}

const line = (o: unknown) => JSON.stringify(o) + "\n";

describe("readAgentSnapshot", () => {
  it("says it is not configured without ECONOMIA_TRADER_STATE_DIR, or when the dir is missing", () => {
    expect(readAgentSnapshot(undefined)).toMatchObject({ configured: false });
    expect(readAgentSnapshot("/nonexistent/economia-trader")).toMatchObject({ configured: false });
  });

  it("reads the book, stops, pending orders, kill switch, decisions and alerts the agent wrote", () => {
    const dir = stateDir({
      "state.json": JSON.stringify({
        mode: "paper",
        exchange: "bybit",
        config_version: "abc123",
        broker: { cash: "991.50" },
        positions: { BTCUSDT: { qty: "0.0002", avg_price: "50000" } },
        stops: { BTCUSDT: "48500" },
        exchange_stops: { BTCUSDT: { order_id: "s-1" } },
        pending: { "o-9": {} },
        realized_today: "0",
        errors_in_row: 1,
      }),
      "journal.jsonl":
        line({ ts: "2026-10-17T10:00:00+00:00", kind: "run", payload: { as_of: "2026-10-17T10:00:00+00:00", version: "abc123" } }) +
        line({ ts: "2026-10-17T10:00:01+00:00", kind: "fill", payload: { side: "buy", qty: "0.0002", symbol: "BTCUSDT", price: "50000", source: "exchange" } }) +
        "{half-written",
      "alerts.jsonl": line({ sent_at: "2026-10-17T10:01:00+00:00", rule: "auto_kill", title: "Auto-kill", detail: "drawdown" }),
      KILL: "",
    });
    const s = readAgentSnapshot(dir, { now: new Date("2026-10-17T10:05:00Z"), staleAfterSeconds: 900 });
    if (!s.configured) throw new Error("expected a configured snapshot");
    expect(s).toMatchObject({ mode: "paper", exchange: "bybit", killSwitch: true, cash: "991.50", pendingOrders: 1, errorsInRow: 1 });
    expect(s.positions).toEqual([{ symbol: "BTCUSDT", qty: "0.0002", avgPrice: "50000", stop: "48500", stopOnExchange: true }]);
    expect(s.lastTick).toEqual({ at: "2026-10-17T10:00:00+00:00", ageSeconds: 300, stale: false });
    expect(s.events[0].text).toBe("fill buy 0.0002 BTCUSDT @ 50000 (exchange)"); // newest first; the broken line is skipped
    expect(s.alerts[0]).toMatchObject({ kind: "auto_kill", text: "Auto-kill: drawdown" });
  });

  it("flags a stale agent when the last tick is older than the threshold", () => {
    const dir = stateDir({
      "journal.jsonl": line({ ts: "2026-10-17T08:00:00+00:00", kind: "run", payload: {} }),
    });
    const s = readAgentSnapshot(dir, { now: new Date("2026-10-17T10:00:00Z"), staleAfterSeconds: 900 });
    expect(s.configured && s.lastTick?.stale).toBe(true);
  });

  it("reads only the end of a huge journal", () => {
    const old = line({ ts: "2026-01-01T00:00:00+00:00", kind: "note", payload: { msg: "x".repeat(200) } }).repeat(4000);
    const dir = stateDir({ "journal.jsonl": old + line({ ts: "2026-10-17T10:00:00+00:00", kind: "run", payload: {} }) });
    const s = readAgentSnapshot(dir, { now: new Date("2026-10-17T10:00:10Z") });
    expect(s.configured && s.lastTick?.at).toBe("2026-10-17T10:00:00+00:00");
  });
});

describe("redaction and summaries", () => {
  it("never lets a credential-looking field through", () => {
    expect(redact({ api_key: "k", nested: { Secret: "s", ok: 1 }, list: [{ token: "t" }] })).toEqual({
      api_key: "***",
      nested: { Secret: "***", ok: 1 },
      list: [{ token: "***" }],
    });
    expect(summarize("error", { error: "boom", signature: "abc" })).toBe("error: boom");
  });

  it("describes the safety events in one line", () => {
    expect(summarize("reconcile_mismatch", { symbol: "BTCUSDT", book: "1", exchange: "0.5", action: "book adjusted down" })).toBe(
      "book vs exchange BTCUSDT: book 1, exchange 0.5 → book adjusted down"
    );
    expect(summarize("stop_client_side", { symbol: "BTCUSDT", why: "mexc" })).toBe("stop stays client-side BTCUSDT: mexc");
    expect(summarize("auto_kill", { reason: "drawdown" })).toBe("AUTO-KILL: drawdown");
    expect(summarize("intent", { side: "buy", qty: "0.0002", symbol: "BTCUSDT", order_type: "market", mode: "paper" })).toBe(
      "intent buy 0.0002 BTCUSDT (market, paper)"
    );
  });
});
