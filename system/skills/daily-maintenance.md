# Daily Maintenance Skill

Use this skill to run Iron Agent's daily idle maintenance. The default job
prepares memory candidates, runs shadow review, and writes a maintenance report.
It keeps high-token memory and evolution work outside live conversation.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Trigger](#trigger)
- [Policy](#policy)
- [Process](#process)
- [Scheduling Options](#scheduling-options)
- [Verification](#verification)

## Read Path From Here

| Need | Next file |
|---|---|
| Maintenance config | `config/maintenance.json` |
| Maintenance script | `system/scripts/daily_maintenance.py` |
| Shadow reviewer | `system/scripts/shadow_reviewer.py` |
| Windows scheduler installer | `system/scripts/install_windows_task.ps1` |
| Codex automation | `system/skills/codex-automation.md` |
| Codex prompt | `system/prompts/codex-shadow-maintenance.md` |
| Memory workflow | `system/skills/memory-maintenance.md` |
| Layered memory | `workspace/memory/INDEX.md` |
| Task log | `workspace/meta/task-log.jsonl` |
| Last run state | `workspace/meta/maintenance-state.json` |
| Reports | `output/maintenance/` |

## Trigger

Run daily maintenance when:

- the user asks to organize memory,
- an external scheduler calls `system/scripts/daily_maintenance.py`,
- the current time is inside the configured idle window,
- at least `min_hours_between_runs` has passed since the last run.

## Policy

- Default permission level is P1.
- Do not call external services.
- Do not delete files.
- Do not auto-merge global memory unless `auto_apply_memory` is true.
- Run shadow review only during scheduled maintenance or explicit user request.
- Always write a task log entry.
- Preserve generated review files for user inspection.

## Process

Run:

```bash
python system/scripts/daily_maintenance.py --root .
```

The script will:

1. Read `config/maintenance.json`.
2. Check the idle window and last run time.
3. Run memory candidate preparation.
4. Run local shadow review to promote deterministic SOP candidates.
5. Optionally apply approved global memory candidates if configured.
6. Write `workspace/meta/maintenance-state.json`.
7. Write `workspace/meta/codex-automation-trigger.json`.
8. Write `output/maintenance/YYYY-MM-DD-daily-maintenance.md`.
9. Append a task log entry.

Use `--force` to run outside the idle window:

```bash
python system/scripts/daily_maintenance.py --root . --force
```

## Scheduling Options

This workspace provides the maintenance job, not the OS scheduler.

Possible schedulers:

- Windows Task Scheduler for local preflight.
- Codex automation for AI shadow review.
- A manually launched local scheduler.
- A future always-on agent process.

For Windows Task Scheduler, point the action to:

```powershell
python {iron-agent-root}\system\scripts\daily_maintenance.py --root {iron-agent-root}
```

To let Iron Agent install the Windows scheduled task after user approval:

```powershell
powershell -ExecutionPolicy Bypass -File {iron-agent-root}\system\scripts\install_windows_task.ps1 -Root {iron-agent-root}
```

Preview without changing Windows:

```powershell
powershell -ExecutionPolicy Bypass -File {iron-agent-root}\system\scripts\install_windows_task.ps1 -Root {iron-agent-root} -DryRun
```

Installer policy:

- Ask the user before running without `-DryRun`.
- Default task name: `IronAgentDailyMaintenance`.
- Default schedule time: `02:30`.
- The task runs as the current Windows user.
- Existing task with the same name is replaced.
- This is P2 because it changes OS scheduler state.

Codex automation policy:

- Create after the Windows task.
- Default name: `Iron Agent Shadow Review`.
- Default schedule time: `02:45`.
- Use `system/prompts/codex-shadow-maintenance.md`.
- Read `workspace/meta/codex-automation-trigger.json`.
- This is P2 because it creates a scheduled model task.

## Verification

After running:

1. Confirm `workspace/meta/maintenance-state.json` was updated.
2. Confirm `workspace/meta/codex-automation-trigger.json` was updated.
3. Confirm `workspace/meta/memory-candidates.md` exists.
4. Confirm `workspace/memory/semantic/sops/` stays structured.
5. Confirm `output/maintenance/` has a report if enabled.
6. For scheduler install, confirm `Get-ScheduledTask -TaskName IronAgentDailyMaintenance`.
7. Confirm Codex automation is active when available.
8. Run `system/scripts/health_check.py`.
