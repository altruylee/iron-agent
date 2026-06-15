# Editor Adapters

## Directory

- [Purpose](#purpose)
- [Supported Tools](#supported-tools)
- [Install](#install)
- [Behavior](#behavior)

## Purpose

Iron Agent can be used by coding agents and AI-enabled editors that read project instruction files and can run local commands.

## Supported Tools

| Tool | Adapter file | Status |
|---|---|---|
| Codex | `AGENTS.md` | First-class |
| Claude Code | `CLAUDE.md` | Supported |
| Cursor | `.cursor/rules/iron-agent.mdc` | Supported |
| VS Code Copilot | `.github/copilot-instructions.md` | Supported |
| Cline | `.clinerules` | Supported |
| Roo Code | `.roo/rules/iron-agent.md` | Supported |

## Install

Install all adapter files into a workspace:

```bash
iron editor install . --tool all
```

Install one adapter:

```bash
iron editor install . --tool cursor
iron editor install . --tool vscode
iron editor install . --tool claude
```

Check adapter status:

```bash
iron editor doctor . --json
```

## Behavior

All adapters enforce the same core behavior:

1. Treat `AGENTS.md` as canonical.
2. Run `python system/scripts/memory_router.py --task "<task>"` before memory reads.
3. Read only returned paths.
4. Keep directory files route-only and low-token.
5. Ask before risky operations.
