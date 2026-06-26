# Silent Automation

## Directory

- [Goal](#goal)
- [Daily Use](#daily-use)
- [Background Maintenance](#background-maintenance)
- [Tool Boundaries](#tool-boundaries)

## Goal

Iron Agent should feel invisible in daily use. The user opens a coding agent and
asks normally. Iron Agent handles memory routing, prompt/rule/SOP
overlays, and nightly organization without requiring the user to remember
commands.

## Daily Use

For every user task, the active AI tool should route internally:

```bash
python system/scripts/memory_router.py --task "<task>" --semantic --json
```

If matching paths are returned, the tool reads only those files and applies the
prompts, rules, SOPs, and preferences as an overlay. If no match is returned, the
tool continues normally and treats the task as new content.

Candidates and conflicts are handled silently: daily maintenance displays them
in the Markdown and HTML reports, does not ask for approval, and uses the newest
stable rule or candidate by default until the user asks to revise or delete it.

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
| WorkBuddy | `WORKBUDDY.md` protocol | OS scheduler |

Editor-specific compatibility files are intentionally out of scope. Iron Agent
keeps the core surface small: Codex, Claude Code, WorkBuddy, and the operating
system scheduler for nightly maintenance.
