# Iron Agent

## Directory

- [What It Is](#what-it-is)
- [Design Principle](#design-principle)
- [Install](#install)
- [Use With Codex](#use-with-codex)
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

## Use With Codex

Open the installed folder with Codex and read `AGENTS.md`. If
`install_status` is `0`, run the initial install flow in
`system/skills/initial-install.md`.

## Memory Model

Memory is split into:

| Layer | Path |
|---|---|
| Short-term | `workspace/memory/short-term/` |
| Episode | `workspace/memory/episodes/` |
| Semantic SOP | `workspace/memory/semantic/sops/` |

Use `workspace/memory/INDEX.md` before reading memory.

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
