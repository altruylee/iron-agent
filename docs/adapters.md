# Agent Adapters

## Directory

- [Purpose](#purpose)
- [Supported Tools](#supported-tools)
- [Install](#install)
- [Behavior](#behavior)

## Purpose

Iron Agent focuses on core coding-agent surfaces. It does not ship editor-specific
compatibility files.

## Supported Tools

| Tool | Adapter file | Status |
|---|---|---|
| Codex | `AGENTS.md` | First-class |
| Claude Code | `CLAUDE.md` | Supported |
| WorkBuddy | `WORKBUDDY.md` | Supported |

## Install

Install all adapter files into a workspace:

```bash
iron adapter install . --tool all
```

Install one adapter:

```bash
iron adapter install . --tool claude
iron adapter install . --tool workbuddy
```

Check adapter status:

```bash
iron adapter doctor . --json
```

## Behavior

All adapters enforce the same core behavior:

1. Treat `AGENTS.md` as canonical.
2. Run `python system/scripts/memory_router.py --task "<task>" --semantic` before memory reads.
3. Read only returned paths.
4. Keep directory files route-only and low-token.
5. Ask before risky operations.
