// economia-trader bridge (network-agents-setup addition): GET /api/agent → read-only snapshot.
import { Router } from "express";
import { readAgentSnapshot } from "../agent.js";

export const agentRouter = Router();

agentRouter.get("/", (_req, res) => {
  const stale = Number(process.env.ECONOMIA_TRADER_STALE_AFTER_S ?? 900);
  res.json(
    readAgentSnapshot(process.env.ECONOMIA_TRADER_STATE_DIR, {
      staleAfterSeconds: Number.isFinite(stale) && stale > 0 ? stale : 900,
    })
  );
});
