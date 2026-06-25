# Iron Agent Workspace Instructions

This folder is a local, file-driven AI workspace for Codex. It is not an app.
Its purpose is to keep accumulated prompts, rules, SOPs, preferences, logs, and
durable memory in predictable places so future AI sessions use fewer tokens and
feel more personalized to the user.

## Directory

- [Start Here](#start-here)
- [First Principle](#first-principle)
- [Installation State](#installation-state)
- [Memory Routing Contract](#memory-routing-contract)
- [Daily Conversation Consolidation](#daily-conversation-consolidation)
- [Pack Roadmap](#pack-roadmap)
- [Navigation Index](#navigation-index)
- [Task Read Paths](#task-read-paths)
- [Operating Rules](#operating-rules)
- [Core Paths](#core-paths)

## Start Here

For every task in this workspace:

1. Before executing the user's task, identify all ambiguous or missing
   requirements, list the questions for user confirmation, and only produce the
   final result after everything necessary is clear.
2. Check [Installation State](#installation-state).
3. If `install_status` is `0`, read and execute `system/skills/initial-install.md`
   before ordinary work.
4. Read `workspace/workspace-config.md`.
5. Read `system/skills/codex-agent.md`.
6. If the user says "continue", "last time", "resume", or similar, read
   `workspace/meta/active-context.md` before doing anything else.
7. For memory/rules, run `python system/scripts/memory_router.py --task "<task>"`.
   If it returns paths, read only those paths and layer the prompts/rules onto
   the user request. If it returns no paths, treat the request as new content
   and continue normally.
8. Route materials and outputs using `wiki/_schema.md`.
9. Record finished work in `workspace/meta/task-log.jsonl` when practical.
10. Update `workspace/meta/active-context.md` when there is useful continuation
   state.

## First Principle

Iron Agent optimizes for precise, low-token navigation.

- Keep every request and response concise and task-relevant.
- Every Markdown file must contain `## Directory`.
- Directory sections are routing only; do not put content or explanations in them.
- Top memory indexes must stay low-token: top <= 50 lines, second level <= 100,
  third level <= 150, single SOP <= 200.
- Every large or multi-file area must be reachable through a tree-like read
  path from `AGENTS.md`.
- Use the directory and read-path tables before broad workspace scans.
- Every content update, memory update, skill install, package integration, and
  evolution pass must preserve directory sections and links.
- After changing core docs, skills, memory, or navigation, run
  `python system/scripts/structure_integrity.py --root .`.

## Runtime Boundaries

- Do not read all memory every round.
- Do not store or merge full chat history.
- Do not run self-evolution or memory consolidation in the live conversation
  unless the user explicitly asks.
- Use `system/scripts/memory_router.py` before reading memory. Default to hot
  memory; warm/cold archives are script-routed only.
- A routing miss is not an error during normal work. Continue with the user's
  request and record useful prompt/rule candidates for nightly maintenance.
- If context is missing, output `[缺少前置条件：请补充XX]` and stop.
- Do not restate the user's original request in the answer.

## Memory Routing Contract

Memory/rule lookup flow:

1. User question.
2. Run `python system/scripts/memory_router.py --task "<task>"`.
3. If paths are returned, read the returned 1-5 paths.
4. Apply relevant prompts, rules, preferences, and SOPs as an overlay on the
   user's current request.
5. If no paths are returned, answer normally as new content and add concise
   candidates to task logs or friction logs when useful.
6. Nightly maintenance organizes candidates into prompts/rules/SOPs and reports
   what changed to the user.

Rules:

- `AGENTS.md` and `workspace/memory/INDEX.md` answer only which class to enter.
- Detailed information belongs only in leaf files.
- If an index exceeds its line limit, split it or move cold entries to `cold/`.
- Do not block normal conversation just because no matching directory exists.

## Daily Conversation Consolidation

Canonical policy:

- 日常对话不打断用户。
- Codex 在执行任务时，只记录必要的结构化痕迹。
- 每天定时任务统一整理当天 workspace 痕迹。
- 不保存完整聊天记录，只沉淀稳定偏好、规则、SOP、项目事实和未完成上下文。

Daily maintenance consolidates the day's workspace traces into memory
candidates. It must not interrupt normal conversations and must not save full
chat history.

1. Scheduled maintenance reads `system/skills/daily-conversation-consolidation.md`.
2. It consolidates today's `workspace/meta/task-log.jsonl`, active context,
   friction log, memory candidates, and maintenance outputs.
3. It writes `output/maintenance/YYYY-MM-DD-conversation-digest.md`.
4. It promotes stable candidates through the normal daily maintenance pipeline.
5. If a platform exports chat transcripts into the workspace, the digest may use
   them; otherwise missing transcript access is normal.

## Installation State

This section is the single source of truth for first-use setup.

- install_status: `0`
- install_skill: `system/skills/initial-install.md`
- installed_at:
- installer_agent:
- profile_version: `0`

Status meanings:

- `0`: not installed. Run `system/skills/initial-install.md` first and collect the user profile.
- `1`: installed. Use the normal task read paths.

After successful installation, update this section:

- set `install_status` to `1`,
- set `installed_at` to the current date/time,
- set `installer_agent` to the agent name if known,
- increment `profile_version` to `1`.

## Navigation Index

Use this index before scanning the repository.

| Need | Next file to read | Why |
|---|---|---|
| First-use installation | `system/skills/initial-install.md` | Collect user profile and set installed state |
| Install this pack | `install.ps1` or `install.py` | Copy Iron Agent to a user target directory |
| Publish this pack | `system/scripts/release_cleanup.py` and `system/scripts/release_check.py` | Clean runtime state and verify public release safety |
| Codex global entry | `codex-global-skill/SKILL.md` | Make Codex discover and enter this workspace |
| Domain agents | `packs/domain-agents/INDEX.md` | Store user-created domain agents and field packs |
| Import user agent file | `system/skills/domain-agent-import.md` | Convert an existing agent file into an enforceable domain agent |
| Understand this workspace | `workspace/workspace-config.md` | Directory map, output contract, enabled skills |
| Execute any task | `system/skills/codex-agent.md` | Workflow, permissions, logging, memory rules |
| Improve the pack | `system/skills/evolution.md` | Detect repeated work and propose new skills |
| Backup or restore | `system/skills/backup-restore.md` | Export or restore user workspace state |
| Update core pack | `system/skills/update-core.md` | Update core files while preserving user data |
| Install skills | `system/skills/skill-installation.md` | Source-first skill install with security audit |
| Integrate engineering packages | `system/skills/engineering-package.md` | Stage and route repo-level packages such as external skill packs |
| Resume previous work | `workspace/meta/active-context.md` | Short-lived continuation anchors |
| Route prompts/rules | `system/scripts/memory_router.py` | Machine-routed low-token overlays |
| Use global durable memory | `workspace/meta/memory.md` | Global preferences only when needed |
| Maintain memory | `system/skills/memory-maintenance.md` | Extract, classify, dedupe, and merge memory candidates |
| Daily conversation consolidation | `system/skills/daily-conversation-consolidation.md` | Summarize today's workspace traces for nightly maintenance |
| Daily idle maintenance | `system/skills/daily-maintenance.md` | Run scheduled housekeeping and memory preparation |
| Codex automation | `system/skills/codex-automation.md` | Run scheduled AI shadow review after local preflight |
| Install Windows schedule | `system/scripts/install_windows_task.ps1` | Register daily maintenance in Windows Task Scheduler after user approval |
| Check directory and links | `system/scripts/structure_integrity.py` | Verify Markdown directories and local links |
| Route wiki writes | `wiki/_schema.md` | Raw/source/entity/concept/exploration rules |
| Research a topic | `system/skills/research.md` | Local-first research workflow |
| Use the personal wiki | `system/integrations/personal-wiki.md` | Wiki integration contract |
| Debug repeated workflow issues | `workspace/meta/friction-log.md` | Known friction and fixes |

## Task Read Paths

Follow the shortest matching path.

| Task type | Read path |
|---|---|
| First install | `AGENTS.md` -> `system/skills/initial-install.md` -> `workspace/workspace-config.md` -> `workspace/meta/memory.md` |
| Pack install | `install.ps1` or `install.py` -> `codex-global-skill/SKILL.md` -> target workspace `AGENTS.md` |
| Release publish | `AGENTS.md` -> `system/scripts/release_cleanup.py` -> `system/scripts/release_check.py` |
| General execution | `AGENTS.md` -> `workspace/workspace-config.md` -> `system/skills/codex-agent.md` |
| Prompt/rule lookup | `AGENTS.md` -> `system/scripts/memory_router.py` -> returned paths only -> user request |
| User agent import | `AGENTS.md` -> `system/skills/domain-agent-import.md` -> source agent file -> `packs/domain-agents/INDEX.md` |
| Domain-matched task | `AGENTS.md` -> `system/skills/codex-agent.md` -> `packs/domain-agents/INDEX.md` -> matching `RUNTIME.md` -> matching `RULES.md` |
| Skill install | `AGENTS.md` -> `system/skills/skill-installation.md` -> user-provided source -> `system/scripts/audit_skill.py` |
| Engineering package | `AGENTS.md` -> `system/skills/engineering-package.md` -> package source -> `system/scripts/analyze_package.py` |
| Backup / restore | `AGENTS.md` -> `system/skills/backup-restore.md` -> `system/scripts/backup_workspace.py` |
| Core update | `AGENTS.md` -> `system/skills/update-core.md` -> `system/scripts/update_core.py` |
| Resume | `AGENTS.md` -> `workspace/meta/active-context.md` -> relevant file named in latest entry |
| Ingest material | `AGENTS.md` -> `workspace/workspace-config.md` -> `wiki/_schema.md` -> `system/integrations/personal-wiki.md` |
| Research | `AGENTS.md` -> `workspace/workspace-config.md` -> `system/skills/research.md` -> `wiki/_schema.md` |
| Memory update | `AGENTS.md` -> `system/skills/memory-maintenance.md` -> `workspace/meta/memory.md` -> `workspace/meta/task-log.jsonl` |
| Daily conversation consolidation | `AGENTS.md` -> `system/skills/daily-conversation-consolidation.md` -> `output/maintenance/YYYY-MM-DD-conversation-digest.md` |
| Daily maintenance | `AGENTS.md` -> `system/skills/daily-maintenance.md` -> `config/maintenance.json` -> `system/scripts/daily_maintenance.py` |
| Codex automation install | `AGENTS.md` -> `system/skills/codex-automation.md` -> `system/prompts/codex-shadow-maintenance.md` |
| Windows schedule install | `AGENTS.md` -> `system/skills/daily-maintenance.md` -> `system/scripts/install_windows_task.ps1` |
| Structure integrity | `AGENTS.md` -> `system/scripts/structure_integrity.py` -> changed Markdown files |
| Friction fix | `AGENTS.md` -> `workspace/meta/friction-log.md` -> relevant skill or config |

## Pack Roadmap

Iron Agent is organized as a four-stage Codex workspace pack.

| Stage | Status | Local surface |
|---|---|---|
| 1. Personal usable pack | active | `install.ps1`, `install.py`, `codex-global-skill/`, `system/skills/initial-install.md` |
| 2. Domain agent packs | reserved | `packs/domain-agents/` for user-created field agents |
| 3. Self-evolution | active | `system/skills/evolution.md`, logs, memory maintenance, skill installation |
| 4. Distribution | active | `manifest.json`, `PACK.md`, installer scripts |

## Operating Rules

- Use Chinese when communicating with the user unless the user asks otherwise.
- Do not interrupt normal conversation for memory consolidation; leave only
  necessary structured traces during execution and let daily maintenance
  consolidate them later.
- Keep the user's original Chinese request. Do not translate it to English by
  default; add English keywords only for web search, technical docs, code
  identifiers, library names, or exact error matching.
- Keep requests and responses concise. Avoid emotional wording, filler,
  praise, apologies, and content unrelated to the user's problem.
- Preserve the tree navigation contract: every Markdown file has `## Directory`,
  every important file is reachable from `AGENTS.md`, and links stay current.
- Separate facts, inference, and unverified claims.
- Prefer local files first; use external search only when local context is not
  enough or freshness matters.
- Do not store secrets in this repo. Store only credential hints.
- Ask before P3 actions as defined in `system/skills/codex-agent.md`.

## Core Paths

| Need | Read | Write |
|---|---|---|
| Resume work | `workspace/meta/active-context.md` | `workspace/meta/active-context.md` |
| Ingest material | `wiki/_schema.md` | `wiki/raw/`, `wiki/sources/` |
| Research | `system/skills/research.md`, `wiki/` | `output/research/`, then optionally `wiki/explorations/` |
| Durable memory | `workspace/meta/memory.md` | `workspace/meta/memory.md` |
| Layered memory | `workspace/memory/INDEX.md` | `workspace/memory/short-term/`, `workspace/memory/episodes/`, `workspace/memory/semantic/sops/` |
| Task audit | `workspace/meta/task-log.jsonl` | `workspace/meta/task-log.jsonl` |
| System friction | `workspace/meta/friction-log.md` | `workspace/meta/friction-log.md` |
