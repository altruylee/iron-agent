# Iron Agent

## Directory

- [What It Is](#what-it-is)
- [Design Principle](#design-principle)
- [Install](#install)
- [After Install](#after-install)
- [Quickstart](#quickstart)
- [CLI](#cli)
- [Use With Codex](#use-with-codex)
- [Use With Editors](#use-with-editors)
- [Daily Use Model](#daily-use-model)
- [Silent Automation](#silent-automation)
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

## After Install

Install does not mark onboarding complete. `install_status` stays `0` until the
first AI session collects your stable preferences and writes them into the
workspace.

For Codex, after copying the pack, start a new Codex thread with the installed
folder selected and paste this exact prompt:

```text
初始化 Iron Agent。请先读取 AGENTS.md；如果 install_status 是 0，请执行 system/skills/initial-install.md，分批询问我的稳定偏好、常用路径、工作类型、权限边界和自动化需求。完成写入后再把 install_status 改成 1。
```

Read `OPEN_ME_FIRST.md` if the tool does not prompt automatically.

If you install Iron Agent from inside an existing Codex conversation into a new
folder, Codex cannot silently move the current thread to that new folder. Start a
new Codex thread with the installed folder selected, or install into the folder
that is already open.

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
| `iron init <target>` | Copy a workspace and keep `install_status` at `0` for onboarding |
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
| `iron automation install <root> --tool all --apply` | Install silent adapters and daily maintenance |

## Use With Codex

Open the installed folder with Codex and paste:

```text
初始化 Iron Agent。请先读取 AGENTS.md；如果 install_status 是 0，请执行 system/skills/initial-install.md，分批询问我的稳定偏好、常用路径、工作类型、权限边界和自动化需求。完成写入后再把 install_status 改成 1。
```

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

## Silent Automation

Install once:

```bash
iron automation install . --tool all --apply
iron automation status .
```

After that, daily use should be invisible: the coding agent routes memory before
answering, and nightly maintenance organizes new prompt/rule/SOP candidates in
the background. See `docs/silent-automation.md`.

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
