"""stdio MCP server for plan_runner."""

from __future__ import annotations

import json

from . import tools_impl


def main() -> int:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            json.dumps(
                {
                    "error": "package 'mcp' not installed",
                    "hint": "pip install -r requirements.txt  (from mcp/plan_runner)",
                    "smoke_without_sdk": "python -m mcp_plan_runner.smoke",
                }
            ),
            flush=True,
        )
        return 1

    mcp = FastMCP("plan-runner")

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

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
