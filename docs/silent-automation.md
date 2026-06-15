# Silent Automation

## Directory

- [Goal](#goal)
- [Daily Use](#daily-use)
- [Background Maintenance](#background-maintenance)
- [Tool Boundaries](#tool-boundaries)

## Goal

Iron Agent should feel invisible in daily use. The user opens a coding agent or
editor and asks normally. Iron Agent handles memory routing, prompt/rule/SOP
overlays, and nightly organization without requiring the user to remember
commands.

## Daily Use

For every user task, the active AI tool should route internally:

```bash
python system/scripts/memory_router.py --task "<task>" --json
```

If matching paths are returned, the tool reads only those files and applies the
prompts, rules, SOPs, and preferences as an overlay. If no match is returned, the
tool continues normally and treats the task as new content.

## Background Maintenance

Install silent automation once:

```bash
iron automation install . --tool all --apply
```

On Windows this creates a Task Scheduler entry that runs daily maintenance at
23:30 by default. Use `--time HH:MM` to change the time.

Preview without creating a scheduled task:

```bash
iron automation install . --tool all --json
```

Check status:

```bash
iron automation status . --json
```

## Tool Boundaries

| Tool | Invisible Routing | Invisible Nightly Maintenance |
|---|---|---|
| Codex | `AGENTS.md` protocol and Codex automation | Codex automation or OS scheduler |
| Claude Code | `CLAUDE.md` plus `.claude/settings.json` hooks | Hook and OS scheduler |
| Cursor | Always-on project rules | OS scheduler |
| VS Code Copilot | Copilot instructions plus VS Code tasks | OS scheduler |
| Cline/Roo | Project rule files | OS scheduler |

Cursor and VS Code do not provide the same strong prompt-submit hook surface as
Claude Code. Iron Agent therefore makes their daily behavior invisible through
always-on rules, and makes maintenance invisible through the operating system
scheduler.
