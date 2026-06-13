# Codex Automation Skill

Use this skill when Iron Agent should create, update, or explain Codex
automations for scheduled AI shadow maintenance.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Purpose](#purpose)
- [Two-Stage Schedule](#two-stage-schedule)
- [Creation During Install](#creation-during-install)
- [Runtime Rules](#runtime-rules)
- [Verification](#verification)

## Read Path From Here

| Need | Next file |
|---|---|
| Daily maintenance | `system/skills/daily-maintenance.md` |
| Windows task installer | `system/scripts/install_windows_task.ps1` |
| Codex prompt | `system/prompts/codex-shadow-maintenance.md` |
| Trigger state | `workspace/meta/codex-automation-trigger.json` |
| Layered memory | `workspace/memory/INDEX.md` |

## Purpose

Codex automation is the AI stage. It runs after the Windows local preflight and
uses a model to review only the async queue.

## Two-Stage Schedule

| Stage | Default time | Runner | Role |
|---|---:|---|---|
| Local preflight | `02:30` | Windows Task Scheduler | Run deterministic scripts and write trigger state |
| AI shadow review | `02:45` | Codex automation | Review queued material and promote stable SOPs |

Windows Task Scheduler does not directly call a model. It prepares state. Codex
automation runs independently shortly after and reads that state.

## Creation During Install

During initial install:

1. Ask for approval to create the Windows scheduled task.
2. Run `system/scripts/install_windows_task.ps1`.
3. Create a Codex cron automation in this workspace.
4. Use `system/prompts/codex-shadow-maintenance.md` as the automation prompt.
5. Record the automation name and schedule in `workspace/meta/codex-automation-state.md`.

Default automation:

- name: `Iron Agent Shadow Review`
- workspace: current Iron Agent root
- schedule: daily `02:45`
- model: default Codex model
- reasoning effort: `low`

## Runtime Rules

- Do not read full chat history.
- Do not read all memory.
- Read `workspace/meta/codex-automation-trigger.json` if present.
- Read `workspace/memory/shadow-review/INDEX.md`.
- Process only queued review files and routed SOP targets.
- Run `system/scripts/shadow_reviewer.py`.
- Run `system/scripts/structure_integrity.py` and `system/scripts/health_check.py`.
- If there is no queued work, make no broad changes.

## Verification

After creation:

1. Confirm Windows scheduled task exists.
2. Confirm Codex automation exists and is active.
3. Confirm `workspace/meta/scheduled-task-state.json` after local task runs.
4. Confirm `workspace/meta/codex-automation-trigger.json` after local maintenance runs.
5. Confirm structure and health checks pass.
