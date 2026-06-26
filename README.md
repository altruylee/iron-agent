# Iron Agent

## Directory

- [Why Iron Agent](#why-iron-agent)
- [What It Is](#what-it-is)
- [Design Principle](#design-principle)
- [Install](#install)
- [Upgrade Existing Workspace](#upgrade-existing-workspace)
- [After Install](#after-install)
- [Quickstart](#quickstart)
- [CLI](#cli)
- [Use With Codex](#use-with-codex)
- [Use With Agents](#use-with-agents)
- [Daily Use Model](#daily-use-model)
- [Silent Automation](#silent-automation)
- [Memory Model](#memory-model)
- [Automation](#automation)
- [Release Safety](#release-safety)

## Why Iron Agent

Most AI tools forget you the moment the chat ends. Iron Agent gives them a
memory palace: a disciplined local workspace where your preferences, rules,
SOPs, recurring workflows, and hard-won project context are distilled into a
small, routable layer.

The result is an assistant that feels sharper every day without dragging a giant
history into every prompt. It looks up only what matters, applies the right
personal rules at the right moment, and quietly turns repeated work into reusable
instructions. Codex, Claude Code, and WorkBuddy can all stand on the same
memory layer, so your agent stops being a blank model and starts
behaving like a long-term working partner.

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

Copy Iron Agent into a workspace:

```powershell
python install.py --target {target-folder}
```

Or with PowerShell:

```powershell
.\install.ps1 -Target {target-folder}
```

Then open `{target-folder}` in Codex and paste:

```text
初始化 Iron Agent。请先读取 AGENTS.md；如果 install_status 是 0，请执行 system/skills/initial-install.md，分批询问我的稳定偏好、常用路径、工作类型、权限边界和自动化需求。完成写入后再把 install_status 改成 1。
```

The installer only copies files. `install_status` stays `0` until onboarding is
completed by the first AI session.

## Upgrade Existing Workspace

Use this path when Iron Agent has already been installed and has accumulated
memory, logs, reports, wiki pages, or domain agents. Do not run a fresh install
over an active workspace.

From the existing workspace:

```powershell
iron update . --source {new-pack-path}
python system/scripts/daily_maintenance.py --root . --force
```

`iron update` refreshes the workspace agent files (`AGENTS.md`, `CLAUDE.md`,
`WORKBUDDY.md`) and writes `workspace/meta/agent-refresh-request.md`. A running
chat cannot be force-reloaded by the CLI, so paste or follow the printed refresh
prompt in the current conversation after updating.

`{new-pack-path}` is the folder that contains the newer Iron Agent release, for
example the cloned GitHub repo or a freshly downloaded release folder.

Preview first without changing files:

```powershell
iron update . --source {new-pack-path} --dry-run
```

The updater preserves durable user state by default:

- `workspace/meta/`
- `workspace/memory/`
- `wiki/`
- `packs/domain-agents/`
- `watchlists/`
- `hypotheses/`
- `inbox/`
- `output/`
- `backups/`
- `tools/packages/`

## After Install

If you install into a new folder from an existing Codex thread, start a new Codex
thread with that folder selected. Codex cannot silently switch the current
thread to a newly created workspace.

Read `OPEN_ME_FIRST.md` if the tool does not prompt automatically.

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
| `iron update <root> --source <new-pack>` | Update an existing workspace while preserving user data |
| `iron capture` | Extract `today-chat.md` candidates and run daily maintenance |
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
| `iron adapter install <root> --tool all` | Install Claude/WorkBuddy adapter files |
| `iron automation install <root> --tool all --apply` | Install silent adapters and daily maintenance |

## Use With Codex

Open the installed folder with Codex and paste:

```text
初始化 Iron Agent。请先读取 AGENTS.md；如果 install_status 是 0，请执行 system/skills/initial-install.md，分批询问我的稳定偏好、常用路径、工作类型、权限边界和自动化需求。完成写入后再把 install_status 改成 1。
```

## Use With Agents

Codex uses `AGENTS.md` directly. Claude Code and WorkBuddy use their own adapter
files.

### Claude Code

Fresh install already includes Claude Code files:

```text
CLAUDE.md
.claude/settings.json
```

Open `{target-folder}` in Claude Code. Claude should read `CLAUDE.md`, route
memory first, and use the same Iron Agent workspace.

For an existing workspace, install only the Claude adapter:

```bash
iron adapter install . --tool claude
```

### WorkBuddy

Fresh install already includes:

```text
WORKBUDDY.md
```

Open `{target-folder}` in WorkBuddy. WorkBuddy should read `WORKBUDDY.md`, route
memory first, and use the same Iron Agent workspace.

For an existing workspace, install only the WorkBuddy adapter:

```bash
iron adapter install . --tool workbuddy
```

### All Adapters

Install or refresh all adapter instruction files:

```bash
iron adapter install . --tool all
iron adapter doctor . --json
```

Supported adapters:

| Tool | File |
|---|---|
| Claude Code | `CLAUDE.md` |
| WorkBuddy | `WORKBUDDY.md` |

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

Manual capture is available when the user wants to actively consolidate a
conversation:

```powershell
iron capture
```

By default, this reads `today-chat.md` in the current workspace, uses
`YYYY-MM-DD daily chat` as the title, extracts only stable preferences, rules,
SOP candidates, project facts, and unfinished context, then runs:

```powershell
python system/scripts/daily_maintenance.py --root . --force
```

It does not store the full chat text. Advanced usage:

```powershell
iron capture . --file .\chat.md --title "today's planning"
iron capture . --text "以后默认先问清楚模糊需求。"
iron capture . --file .\chat.md --no-maintenance
```

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
