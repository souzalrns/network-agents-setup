"""Teste real do MCP server via JSON-RPC.

Arranca o server como subprocess, envia 'initialize' + 'tools/list' +
'tools/call' (list_templates), e imprime as respostas.

Isto prova que o server responde a JSON-RPC a serio.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _send(proc, obj):
    line = json.dumps(obj) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()


def _read_response(proc, expected_id):
    """Le linhas do stdout ate encontrar a resposta com o id esperado."""
    for _ in range(50):
        line = proc.stdout.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            print(f"  [non-JSON line]: {line[:120]}")
            continue
        if msg.get("id") == expected_id:
            return msg
    return None


def main() -> int:
    env = os.environ.copy()
    env["PLAN_RUNNER_REPO_ROOT"] = str(HERE.parent.parent)
    env["PLAN_RUNNER_MCP_PROFILE"] = "permissive"  # lab only
    env["PLAN_RUNNER_MCP_KEY"] = "sk_lab_change_me"

    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_plan_runner"],
        cwd=str(HERE),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    try:
        # 1. initialize
        print("[1] initialize")
        _send(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1"},
            },
        })
        resp = _read_response(proc, 1)
        if not resp:
            print("  ERRO: sem resposta a initialize")
            return 1
        server_info = resp.get("result", {}).get("serverInfo", {})
        print(f"  server: {server_info.get('name')} v{server_info.get('version', '?')}")
        print(f"  capabilities: {list(resp.get('result', {}).get('capabilities', {}).keys())}")

        # 2. notifications/initialized
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 3. tools/list
        print()
        print("[2] tools/list")
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        resp = _read_response(proc, 2)
        if not resp:
            print("  ERRO: sem resposta a tools/list")
            return 1
        tools = resp.get("result", {}).get("tools", [])
        print(f"  {len(tools)} tools:")
        for t in tools:
            print(f"    - {t.get('name')}: {t.get('description', '')[:60]}")

        # 4. tools/call list_templates
        print()
        print("[3] tools/call -> list_templates")
        _send(proc, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list_templates", "arguments": {}},
        })
        resp = _read_response(proc, 3)
        if not resp:
            print("  ERRO: sem resposta a tools/call")
            return 1
        content = resp.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            try:
                data = json.loads(text)
                print(f"  ok: {data.get('ok')}")
                count = data.get("count", "?")
                print(f"  count: {count}")
                for t in (data.get("templates") or [])[:10]:
                    print(f"    - {t}")
            except json.JSONDecodeError:
                print(f"  raw: {text[:200]}")
        else:
            print(f"  resp: {json.dumps(resp)[:200]}")

        print()
        print("=== TEST PASSED ===")
        return 0

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
