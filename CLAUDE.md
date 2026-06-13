# Iron Agent Workspace Instructions

This file mirrors `AGENTS.md` for Claude-compatible agents. Keep both files
aligned when changing workspace rules.

## Directory

- [Navigation](#navigation)
- [Task Protocol](#task-protocol)
- [Rules](#rules)

## Navigation

Use `AGENTS.md` as the canonical top-level index. From there, follow the
shortest task read path instead of scanning the full workspace.

| Need | Next file |
|---|---|
| First-use installation | `system/skills/initial-install.md` |
| Workspace map | `workspace/workspace-config.md` |
| Execution protocol | `system/skills/codex-agent.md` |
| Resume state | `workspace/meta/active-context.md` |
| Wiki routing | `wiki/_schema.md` |
| Research workflow | `system/skills/research.md` |

## Task Protocol

For every task:

1. Check `AGENTS.md` -> `Installation State`.
2. If `install_status` is `0`, execute `system/skills/initial-install.md`.
3. Read `workspace/workspace-config.md`.
4. Read `system/skills/codex-agent.md`.
5. Read `workspace/meta/active-context.md` first when the user asks to resume.
6. Route knowledge through `wiki/_schema.md`.
7. Write task logs to `workspace/meta/task-log.jsonl`.
8. Update `workspace/meta/active-context.md` when there is continuation state.

## Rules

Use Chinese by default. Separate facts, inference, and unverified claims. Ask
before high-risk operations.
