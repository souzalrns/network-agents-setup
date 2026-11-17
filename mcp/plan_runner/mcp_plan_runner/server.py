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
    def resume_plan(out_dir: str, decision: str = "", gate: str = "") -> str:
        """Resume a paused run. Requires resume scope.

        A human gate is decided only with an explicit decision (approve|reject|edit); pass `gate`
        (the step id) when more than one approval is pending. Without a decision the run only
        continues work that does not wait for a person: a gate is never approved by default (M-010).
        """
        return json.dumps(
            tools_impl.resume_plan(out_dir, decision=decision or None, gate=gate or None),
            ensure_ascii=False,
        )

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
