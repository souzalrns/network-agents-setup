---
name: git-guardrails-claude-code
description: Set up a Claude Code hook that blocks force pushes, pushes to main, rebase and other history-rewriting or work-destroying git commands before they execute. Use when the user wants git safety hooks or to enforce "no --force, no rebase".
---

# Setup Git Guardrails

> Adapted for network-agents-setup from mattpocock/skills (MIT). The upstream hook blocks every `git push`;
> this one lets a normal push to a feature branch through, because the PR workflow needs it, and blocks
> what the maestro's rules forbid ("sem --force, sem rebase", no direct push to `main`).

Sets up a PreToolUse hook that intercepts and blocks dangerous git commands before Claude executes them.

## What Gets Blocked

- force pushes: `git push --force`, `-f` (also inside combined flags like `-fu`), `--force-with-lease`,
  `--force-if-includes`, `--mirror`, a `+refspec`
- deleting remote branches: `git push --delete`, `git push origin :branch`, `--prune`
- pushing to `main` or `master` directly (`git push origin main`, `x:main`, or a bare push while on main)
- history rewrites: `git rebase`, `git filter-branch`, `git filter-repo`
- throwing work away: `git reset --hard`, `git clean -f…`, `git branch -D`, `git checkout .`, `git restore .`

Still allowed: `git push -u origin <feature-branch>`, `git reset --soft`, `git clean -n`, `git branch -d`,
`git checkout <branch>`. Commands are split on `;`, `&&`, `||` and `|`, so a dangerous one chained after a
safe one is still caught; text inside quotes (a commit message, an `echo`) is not mistaken for a command.

When blocked, Claude sees a message telling it the maestro has not authorised the command.

## Steps

### 1. Ask scope

Ask the user: install for **this project only** (`.claude/settings.json`) or **all projects** (`~/.claude/settings.json`)?

### 2. Copy the hook script

The bundled script is at: [scripts/block-dangerous-git.py](scripts/block-dangerous-git.py) (Python 3, stdlib only).

Copy it to the target location based on scope:

- **Project**: `.claude/hooks/block-dangerous-git.py`
- **Global**: `~/.claude/hooks/block-dangerous-git.py`

Make it executable with `chmod +x`.

### 3. Add hook to settings

Add to the appropriate settings file:

**Project** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.py"
          }
        ]
      }
    ]
  }
}
```

**Global** (`~/.claude/settings.json`): the same, with `"command": "python3 ~/.claude/hooks/block-dangerous-git.py"`.

If the settings file already exists, merge the hook into the existing `hooks.PreToolUse` array (create the
array if only `PostToolUse` exists, as in network-agents-setup). Don't overwrite other settings or hooks.

### 4. Ask about customization

Ask if the user wants to add or remove anything from the blocked list. Edit the copied script accordingly
(`PROTECTED` holds the protected branch names).

### 5. Verify

Run a quick test of one blocked and one allowed command:

```bash
echo '{"tool_input":{"command":"git push --force origin feat/x"}}' | python3 <path-to-script>; echo "exit=$?"   # 2, BLOCKED
echo '{"tool_input":{"command":"git push -u origin feat/x"}}' | python3 <path-to-script>; echo "exit=$?"      # 0
```
