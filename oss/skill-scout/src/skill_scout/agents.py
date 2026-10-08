"""Agent → project skills folder, so `--agent codex` installs where Codex looks.

Data imported from the skills CLI 1.7.1 (vercel-labs/skills, MIT), `agents` table, project
scope (`skillsDir`). Many agents share the universal `.agents/skills` folder: installing there
once serves all of them. `claude` is an alias of `claude-code`, the default.
"""

from __future__ import annotations

from .errors import UsageError

DEFAULT_AGENT = "claude-code"
ALIASES = {"claude": "claude-code", "copilot": "github-copilot", "gemini": "gemini-cli"}

# name: (display name, project skills folder)
AGENTS: dict[str, tuple[str, str]] = {
    "aider-desk": ("AiderDesk", ".aider-desk/skills"),
    "amp": ("Amp", ".agents/skills"),
    "antigravity": ("Antigravity", ".agents/skills"),
    "antigravity-cli": ("Antigravity CLI", ".agents/skills"),
    "astrbot": ("AstrBot", "data/skills"),
    "autohand-code": ("Autohand Code CLI", ".autohand/skills"),
    "augment": ("Augment", ".augment/skills"),
    "bob": ("IBM Bob", ".bob/skills"),
    "claude-code": ("Claude Code", ".claude/skills"),
    "openclaw": ("OpenClaw", "skills"),
    "cline": ("Cline", ".agents/skills"),
    "codearts-agent": ("CodeArts Agent", ".codeartsdoer/skills"),
    "codebuddy": ("CodeBuddy", ".codebuddy/skills"),
    "codemaker": ("Codemaker", ".codemaker/skills"),
    "codestudio": ("Code Studio", ".codestudio/skills"),
    "codex": ("Codex", ".agents/skills"),
    "command-code": ("Command Code", ".commandcode/skills"),
    "continue": ("Continue", ".continue/skills"),
    "cortex": ("Cortex Code", ".cortex/skills"),
    "crush": ("Crush", ".crush/skills"),
    "cursor": ("Cursor", ".agents/skills"),
    "deepagents": ("Deep Agents", ".agents/skills"),
    "devin": ("Devin for Terminal", ".devin/skills"),
    "dexto": ("Dexto", ".agents/skills"),
    "droid": ("Droid", ".agents/skills"),
    "eve": ("Eve", "agent/skills"),
    "firebender": ("Firebender", ".agents/skills"),
    "forgecode": ("ForgeCode", ".forge/skills"),
    "fx": ("fx", ".fx/skills"),
    "gemini-cli": ("Gemini CLI", ".agents/skills"),
    "github-copilot": ("GitHub Copilot", ".agents/skills"),
    "goose": ("Goose", ".goose/skills"),
    "grok": ("Grok Build", ".grok/skills"),
    "hermes-agent": ("Hermes Agent", ".hermes/skills"),
    "inference-sh": ("inference.sh", ".inferencesh/skills"),
    "jazz": ("Jazz", ".jazz/skills"),
    "junie": ("Junie", ".junie/skills"),
    "iflow-cli": ("iFlow CLI", ".iflow/skills"),
    "kilo": ("Kilo Code", ".agents/skills"),
    "kimchi": ("Kimchi", ".kimchi/skills"),
    "kimi-code-cli": ("Kimi Code CLI", ".agents/skills"),
    "kiro-cli": ("Kiro CLI", ".kiro/skills"),
    "kode": ("Kode", ".kode/skills"),
    "lingma": ("Lingma", ".lingma/skills"),
    "loaf": ("Loaf", ".agents/skills"),
    "mcpjam": ("MCPJam", ".mcpjam/skills"),
    "minimax-code": ("MiniMax Code", ".minimax/skills"),
    "mistral-vibe": ("Mistral Vibe", ".vibe/skills"),
    "moxby": ("Moxby", ".moxby/skills"),
    "mux": ("Mux", ".mux/skills"),
    "opencode": ("OpenCode", ".agents/skills"),
    "openhands": ("OpenHands", ".openhands/skills"),
    "ona": ("Ona", ".ona/skills"),
    "pi": ("Pi", ".agents/skills"),
    "posit-assistant": ("Posit Assistant", ".posit/assistant/skills"),
    "qoder": ("Qoder", ".qoder/skills"),
    "qoder-cn": ("Qoder CN", ".qoder/skills"),
    "qwen-code": ("Qwen Code", ".qwen/skills"),
    "replit": ("Replit", ".agents/skills"),
    "reasonix": ("Reasonix", ".reasonix/skills"),
    "rovodev": ("Rovo Dev", ".rovodev/skills"),
    "roo": ("Roo Code", ".roo/skills"),
    "sarvam-code": ("Sarvam Code", ".agents/skills"),
    "tabnine-cli": ("Tabnine CLI", ".tabnine/agent/skills"),
    "terramind": ("Terramind", ".terramind/skills"),
    "tinycloud": ("Tinycloud", ".tinycloud/skills"),
    "trae": ("Trae", ".trae/skills"),
    "trae-cn": ("Trae CN", ".trae/skills"),
    "warp": ("Warp", ".agents/skills"),
    "windsurf": ("Windsurf", ".windsurf/skills"),
    "zed": ("Zed", ".agents/skills"),
    "zcode": ("ZCode", ".zcode/skills"),
    "zencoder": ("Zencoder", ".zencoder/skills"),
    "zenflow": ("Zenflow", ".zencoder/skills"),
    "neovate": ("Neovate", ".neovate/skills"),
    "pochi": ("Pochi", ".pochi/skills"),
    "promptscript": ("PromptScript", ".agents/skills"),
    "adal": ("AdaL", ".adal/skills"),
    "universal": ("Universal", ".agents/skills"),
}


def skills_dir(agent: str) -> str:
    """Project skills folder of `agent` (relative to the project root)."""
    key = ALIASES.get(agent, agent)
    if key not in AGENTS:
        raise UsageError(f"unknown agent {agent!r}; known: {', '.join(sorted(AGENTS))}")
    return AGENTS[key][1]


def dests_for(agents: list[str] | None) -> list[str]:
    """Distinct folders for these agents, in order (agents sharing a folder get one install)."""
    out: list[str] = []
    for agent in agents or [DEFAULT_AGENT]:
        d = skills_dir(agent)
        if d not in out:
            out.append(d)
    return out
