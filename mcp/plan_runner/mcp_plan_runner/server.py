"""stdio MCP server for plan_runner."""

from __future__ import annotations

import json

from . import tools_impl


def main() -> int:
    MCPServerClass = None
    try:
        # mcp 2.x
        from mcp.server.mcpserver import MCPServer as MCPServerClass
    except ImportError:
        try:
            # mcp 1.x (FastMCP was the old name)
            from mcp.server.fastmcp import FastMCP as MCPServerClass  # type: ignore
        except ImportError:
            print(
                json.dumps(
                    {
                        "error": "package 'mcp' not installed (neither MCPServer nor FastMCP found)",
                        "hint": "pip install -r requirements.txt  (from mcp/plan_runner)",
                        "smoke_without_sdk": "python -m mcp_plan_runner.smoke",
                    }
                ),
                flush=True,
            )
            return 1

    mcp = MCPServerClass("plan-runner")

    @mcp.tool()
    def list_templates() -> str:
        """List plan YAML templates under docs/orchestration."""
        return json.dumps(tools_impl.list_templates(), ensure_ascii=False)

    @mcp.tool()
    def get_status(out_dir: str) -> str:
        """Read status.json for a pilot/run directory (path relative to repo root)."""
        return json.dumps(tools_impl.get_status(out_dir), ensure_ascii=False)

    @mcp.tool()
    def run_plan(plan: str, mode: str = "stub", out: str = "") -> str:
        """Run a plan.yaml (modes: dry-run, stub, external). Requires execute scope."""
        return json.dumps(
            tools_impl.run_plan(plan, mode=mode, out=out or None),
            ensure_ascii=False,
        )

    @mcp.tool()
    def resume_plan(out_dir: str, decision: str = "approve") -> str:
        """Resume paused run (approve|reject|edit). Requires resume scope."""
        return json.dumps(tools_impl.resume_plan(out_dir, decision=decision), ensure_ascii=False)

    @mcp.tool()
    def council_get_request(session_dir: str, provider: str, key: str = "") -> str:
        """Council (M-011): read the request for your position (topic, context, answer format). `provider` is your
        id in config/council-providers.yaml; `key` only if your entry has key_env."""
        return json.dumps(tools_impl.council_get_request(session_dir, provider, key), ensure_ascii=False)

    @mcp.tool()
    def council_submit_position(session_dir: str, provider: str, position: str, key: str = "") -> str:
        """Council (M-011): submit your position as JSON text: {"vote": "approve|conditional|reject|defer",
        "confidence": 0-1, "position": "...", "arguments": [], "risks": [], "conditions": [], "kill_criteria": [],
        "veto": false, "veto_reason": null}. One submission per IA per round. Requires submit scope."""
        return json.dumps(tools_impl.council_submit_position(session_dir, provider, position, key), ensure_ascii=False)

    @mcp.tool()
    def council_status(session_dir: str) -> str:
        """Council (M-011): public status of a council session (phase, round, panel mode, who is still missing)."""
        return json.dumps(tools_impl.council_status(session_dir), ensure_ascii=False)

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
