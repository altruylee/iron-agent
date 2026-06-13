# Workspace Config

## Directory

- [Identity](#identity)
- [Read Path From Here](#read-path-from-here)
- [Directory Map](#directory-map)
- [Default Output Contract](#default-output-contract)
- [Memory Architecture](#memory-architecture)
- [Source Labels](#source-labels)
- [User Profile Slots](#user-profile-slots)
- [Pack Surfaces](#pack-surfaces)
- [Enabled Base Skills](#enabled-base-skills)

## Identity

- name: `iron-agent`
- type: `local-file-driven-ai-workspace`
- language: `zh-CN`
- primary_use: `Codex execution, research, knowledge capture, task logs, durable memory`

## Read Path From Here

| Need | Next file |
|---|---|
| First-use setup | `system/skills/initial-install.md` |
| Install pack elsewhere | `install.ps1` or `install.py` |
| Prepare public release | `system/scripts/release_cleanup.py` -> `system/scripts/release_check.py` |
| Codex global skill | `codex-global-skill/SKILL.md` |
| Domain agents | `packs/domain-agents/INDEX.md` |
| Import user agent file | `system/skills/domain-agent-import.md` |
| Execute safely | `system/skills/codex-agent.md` |
| Evolve repeated workflows | `system/skills/evolution.md` |
| Backup or restore workspace | `system/skills/backup-restore.md` |
| Update core pack files | `system/skills/update-core.md` |
| Install a skill | `system/skills/skill-installation.md` |
| Integrate engineering package | `system/skills/engineering-package.md` |
| Verify directory and links | `system/scripts/structure_integrity.py` |
| Route layered memory | `workspace/memory/INDEX.md` |
| Resume work | `workspace/meta/active-context.md` |
| Update durable memory | `workspace/meta/memory.md` |
| Maintain memory from logs | `system/skills/memory-maintenance.md` |
| Daily idle maintenance | `system/skills/daily-maintenance.md` |
| Codex AI shadow review | `system/skills/codex-automation.md` |
| Route wiki content | `wiki/_schema.md` |
| Research | `system/skills/research.md` |
| Understand wiki integration | `system/integrations/personal-wiki.md` |
| Inspect repeated issues | `workspace/meta/friction-log.md` |

## Directory Map

| Directory | Purpose |
|---|---|
| `inbox/` | Temporary incoming materials |
| `wiki/raw/` | Raw materials preserved with minimal editing |
| `wiki/sources/` | Structured summaries of single sources |
| `wiki/entities/` | People, companies, products, projects, organizations |
| `wiki/concepts/` | Reusable concepts, frameworks, and topics |
| `wiki/explorations/` | Cross-source judgments and tentative theses |
| `output/` | Reports, drafts, task outputs, research deliverables |
| `watchlists/` | Watchlists and recurring monitoring targets |
| `hypotheses/` | Hypotheses, evidence, and review notes |
| `system/skills/` | Workspace skills and operating protocols |
| `system/integrations/` | Integration contracts for optional tools |
| `system/scripts/` | Small deterministic helper scripts |
| `workspace/meta/` | Active context, logs, memory, and friction records |
| `workspace/memory/` | Three-layer routed memory: short-term, episodes, semantic SOPs |
| `tools/` | Optional external or vendored tools |
| `tools/packages/` | Staged engineering-level packages and external repos |
| `backups/` | Local backup archives, excluded from installer output |
| `config/` | Local non-secret config templates |
| `packs/domain-agents/` | User-created domain agents and field packs |
| `codex-global-skill/` | Optional Codex global skill entrypoint |

## Default Output Contract

When producing reports or research outputs, include:

1. Core conclusion.
2. Key evidence.
3. Counter-evidence or risks.
4. Open questions.
5. Next actions.
6. `Wiki check`: what local wiki files were checked and whether they were useful.

## Memory Architecture

| Layer | Path | Use |
|---|---|---|
| Short-Term Memory | `workspace/memory/short-term/` | Minimal current-session cache |
| Episode Memory | `workspace/memory/episodes/` | Topic fragments routed by directory |
| Semantic Memory | `workspace/memory/semantic/sops/` | Fixed SOP rule library |
| Shadow Review | `workspace/memory/shadow-review/` | Async review queue, not live context |

Default execution reads `workspace/memory/INDEX.md`, then only the matched
branch. Do not read all memory by default.

## Source Labels

- `[local]`: from files in this workspace.
- `[web]`: from external web sources.
- `[data]`: from configured data APIs.
- `[inference]`: agent reasoning.
- `[unverified]`: still needs confirmation.

## User Profile Slots

These fields are filled during `system/skills/initial-install.md`. Keep values
short so future agents can read them quickly.

- user_display_name:
- preferred_language: `zh-CN`
- communication_style:
- main_work_types:
- important_paths:
- default_output_style:
- default_permission_preference:
- common_data_sources:
- recurring_tasks:
- never_do_without_confirmation:

## Pack Surfaces

| Surface | Purpose |
|---|---|
| `install.ps1` | Windows installer for creating a user workspace copy |
| `install.py` | Cross-platform installer for creating a user workspace copy |
| `codex-global-skill/SKILL.md` | Optional global Codex skill that routes user requests into Iron Agent |
| `packs/domain-agents/` | Reserved folder for user-created domain agents |
| `system/skills/domain-agent-import.md` | Imports user-provided agent files as enforceable domain agents |
| `system/skills/codex-automation.md` | Creates the scheduled Codex AI shadow review |
| `system/prompts/codex-shadow-maintenance.md` | Prompt used by Codex shadow review automation |
| `system/scripts/structure_integrity.py` | Verifies Markdown directories and local links |
| `manifest.json` | Distribution metadata and required file list |
| `PACK.md` | Human-readable pack overview and release surface |
| `README.md` | Public GitHub overview |
| `SECURITY.md` | Security policy |
| `CONTRIBUTING.md` | Contribution guide |
| `CHANGELOG.md` | Release notes |

## Enabled Base Skills

### initial-install

- status: `enabled`
- path: `system/skills/initial-install.md`
- role: first-use questionnaire, profile capture, and install status update.

### codex-agent

- status: `enabled`
- path: `system/skills/codex-agent.md`
- role: permission, execution, concise communication, structure integrity, logging, and memory protocol.

### domain-agent-import

- status: `enabled`
- path: `system/skills/domain-agent-import.md`
- import_script: `system/scripts/import_domain_agent.py`
- router: `system/scripts/domain_agent_router.py`
- registry: `packs/domain-agents/INDEX.md`
- role: import existing user agent files into registered domain agents with runtime rules.

### memory-maintenance

- status: `enabled`
- path: `system/skills/memory-maintenance.md`
- script: `system/scripts/compact_memory.py`
- router: `system/scripts/memory_router.py`
- shadow_reviewer: `system/scripts/shadow_reviewer.py`
- role: async extraction and SOP promotion outside the live response path.

### skill-installation

- status: `enabled`
- path: `system/skills/skill-installation.md`
- audit_script: `system/scripts/audit_skill.py`
- install_script: `system/scripts/install_skill.py`
- role: install workspace skills from user-provided sources after security audit.

### engineering-package

- status: `enabled`
- path: `system/skills/engineering-package.md`
- analyzer: `system/scripts/analyze_package.py`
- staging_script: `system/scripts/stage_package.py`
- registry: `workspace/meta/package-registry.json`
- role: stage, analyze, audit, and route engineering-level packages.

### evolution

- status: `enabled`
- path: `system/skills/evolution.md`
- script: `system/scripts/evolution_report.py`
- role: detect repeated workflows, propose new skills, and guide pack improvement.

### backup-restore

- status: `enabled`
- path: `system/skills/backup-restore.md`
- backup_script: `system/scripts/backup_workspace.py`
- restore_script: `system/scripts/restore_workspace.py`
- role: backup and restore durable user state.

### update-core

- status: `enabled`
- path: `system/skills/update-core.md`
- script: `system/scripts/update_core.py`
- role: update core pack files while preserving user data.

### daily-maintenance

- status: `enabled`
- path: `system/skills/daily-maintenance.md`
- script: `system/scripts/daily_maintenance.py`
- windows_task_installer: `system/scripts/install_windows_task.ps1`
- config: `config/maintenance.json`
- role: daily idle housekeeping and memory candidate preparation.

### codex-automation

- status: `enabled`
- path: `system/skills/codex-automation.md`
- prompt: `system/prompts/codex-shadow-maintenance.md`
- trigger_state: `workspace/meta/codex-automation-trigger.json`
- default_schedule: daily `02:45`
- role: AI shadow review after Windows local preflight.

### personal wiki

- status: `enabled`
- schema: `wiki/_schema.md`
- raw_dir: `wiki/raw/`
- sources_dir: `wiki/sources/`
- entities_dir: `wiki/entities/`
- concepts_dir: `wiki/concepts/`
- explorations_dir: `wiki/explorations/`

### research

- status: `enabled`
- path: `system/skills/research.md`
- reads_from: `wiki/`, optional web search, optional configured data sources.
- writes_to: `output/research/`, optionally `wiki/explorations/` after user confirmation.
