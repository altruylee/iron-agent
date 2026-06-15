# Iron Agent

## Directory

- [What It Is](#what-it-is)
- [Design Principle](#design-principle)
- [Install](#install)
- [Quickstart](#quickstart)
- [CLI](#cli)
- [Use With Codex](#use-with-codex)
- [Use With Editors](#use-with-editors)
- [Daily Use Model](#daily-use-model)
- [Memory Model](#memory-model)
- [Automation](#automation)
- [Release Safety](#release-safety)

## What It Is

Iron Agent is a local, file-driven workspace for Codex. It is not an app or an
always-on agent runtime. It gives Codex a stable folder structure for task
routing, domain agents, logs, layered memory, SOPs, and optional maintenance.

## Design Principle

Iron Agent optimizes for low-token, precise execution:

- every Markdown file has `## Directory`,
- memory is routed through tree indexes,
- live work reads only the relevant topic branch,
- self-evolution and SOP review run asynchronously,
- external effects require explicit approval.

## Install

CLI:

```bash
python -m pip install -e .
iron --version
```

Python:

```bash
python install.py --target {target-folder}
```

PowerShell:

```powershell
.\install.ps1 -Target {target-folder}
```

Portable dry run:

```bash
python install.py --target {target-folder} --portable --dry-run
```

The installer copies files only. It does not create Windows scheduled tasks or
Codex automations. Those are offered later during initial setup.

## Quickstart

Run the 5 minute path in `QUICKSTART.md`:

```bash
iron init ../iron-agent-demo
iron doctor ../iron-agent-demo --fix
iron report ../iron-agent-demo
```

The full sample is in `examples/end-to-end-demo/`.

## CLI

| Command | Purpose |
|---|---|
| `iron init <target>` | Install a workspace and update `install_status` |
| `iron check <root>` | Validate manifest and release safety |
| `iron doctor <root> --fix` | Diagnose and repair reversible setup issues |
| `iron report <root>` | Generate an evolution report |
| `iron memory route <root> <task>` | Find the smallest relevant memory read path |
| `iron memory slim <root>` | Check low-token memory index limits |
| `iron task list <root>` | Inspect task-log entries |
| `iron web <root> --port 8765` | Start the local dashboard |
| `iron evolve <root> --interactive` | Preview evolution candidates |
| `iron template list` | List starter packs |
| `iron agent new <root> <name>` | Create a domain agent from the template |
| `iron config set <root> evolution.friction_threshold 5` | Adjust evolution thresholds |
| `iron editor install <root> --tool all` | Install Claude/Cursor/VS Code/Cline/Roo rules |

## Use With Codex

Open the installed folder with Codex and read `AGENTS.md`. If
`install_status` is `0`, run the initial install flow in
`system/skills/initial-install.md`.

## Use With Editors

Install adapter instruction files into the workspace:

```bash
iron editor install . --tool all
iron editor doctor . --json
```

Supported adapters:

| Tool | File |
|---|---|
| Claude Code | `CLAUDE.md` |
| Cursor | `.cursor/rules/iron-agent.mdc` |
| VS Code Copilot | `.github/copilot-instructions.md` |
| Cline | `.clinerules` |
| Roo Code | `.roo/rules/iron-agent.md` |

All adapters use the same rule: run `memory_router.py` first, then read only
the returned paths.

## Daily Use Model

Iron Agent stores accumulated prompts, rules, SOPs, and user preferences. During
normal conversation the model first routes the request. If a route is found, it
layers the matching prompts/rules onto the user's request. If no route is found,
it continues normally and leaves concise candidates for nightly organization.

See `docs/daily-use-model.md`.

## Memory Model

Memory is split into:

| Layer | Path |
|---|---|
| Short-term | `workspace/memory/short-term/` |
| Episode | `workspace/memory/episodes/` |
| Semantic SOP | `workspace/memory/semantic/sops/` |

Use `python system/scripts/memory_router.py --task "<task>"` before reading memory.

## Automation

Optional two-stage maintenance:

| Stage | Runner | Default |
|---|---|---|
| Local preflight | Windows Task Scheduler | `02:30` |
| AI shadow review | Codex automation | `02:45` |

Both require explicit user approval.

## Release Safety

Before publishing a fork:

```bash
python system/scripts/release_cleanup.py --root . --apply
python system/scripts/release_check.py --root .
```
