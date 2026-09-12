"""Smoke test tools without MCP SDK / without stdio client.

  python -m mcp_plan_runner.smoke
"""

from __future__ import annotations

import json
import sys

from . import tools_impl
from .policy import repo_root


def main() -> int:
    print("repo_root:", repo_root())
    t = tools_impl.list_templates()
    print("list_templates:", json.dumps(t, ensure_ascii=False)[:500], "...")
    if not t.get("ok"):
        return 1
    templates = t.get("templates") or []
    demo = next((x for x in templates if "design-flow-demo" in x), None)
    demo = demo or next((x for x in templates if x.endswith(".plan.yaml")), None)
    if not demo:
        print("no templates found")
        return 1
    out = "pilots/run-mcp-smoke"
    r = tools_impl.run_plan(demo, mode="dry-run", out=out)
    print("run_plan dry-run:", json.dumps(r, ensure_ascii=False)[:800])
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
