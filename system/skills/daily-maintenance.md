# Daily Maintenance Skill

Use this skill to run Iron Agent's daily idle maintenance. The default job
organizes day-to-day conversation traces into prompts, rules, SOPs, indexes, and
reports. It keeps high-token organization outside live conversation.

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
| Daily conversation consolidation | `system/skills/daily-conversation-consolidation.md` |
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
- Tell the user what was organized: new prompts, new rules, moved indexes,
  displayed candidates, and potential conflicts.
- Candidate memory does not require approval. Display it; let the user request
  deletion or correction later.
- Potential conflicts do not block maintenance. The latest stable rule or
  candidate wins by default, and the conflict must be shown in the report.
- Include the token savings estimate from the maintenance report.
- The final output must return both the long-term report index
  `output/maintenance/index.html` and the latest daily HTML report
  `output/maintenance/YYYY-MM-DD-daily-maintenance.html`.
- Include the safe workspace upgrade command:
  `iron update . --source <new-pack-path>`.

## Process

Run:

```bash
python system/scripts/daily_maintenance.py --root .
```

The script will:

1. Read `config/maintenance.json`.
2. Check the idle window and last run time.
3. Run memory candidate preparation.
4. Generate `output/maintenance/YYYY-MM-DD-conversation-digest.md` from today's
   workspace traces.
5. Run local shadow review to promote deterministic prompt/rule/SOP candidates.
6. Slim indexes and keep top-level routing low-token.
7. Rebuild `workspace/memory/semantic_index.jsonl` and
   `workspace/memory/semantic_vectors.jsonl`.
8. Detect potential memory conflicts and apply the latest-wins default.
9. Estimate tokens avoided by routing first instead of reading all memory.
10. Optionally apply global memory candidates if configured.
11. Write `workspace/meta/maintenance-state.json`.
12. Write `workspace/meta/codex-automation-trigger.json`.
13. Write `output/maintenance/YYYY-MM-DD-daily-maintenance.md`.
14. Write `output/maintenance/YYYY-MM-DD-daily-maintenance.html`.
15. Update `output/maintenance/index.html`.
16. Update `output/maintenance/maintenance-history.json`.
17. Append a task log entry.
18. Surface a concise user notice from the maintenance report.
19. Return `output/maintenance/index.html` and the latest daily HTML report path.
20. Remind the user that existing workspaces can be updated with
    `iron update . --source <new-pack-path>` without replacing accumulated data.

Token estimates use `4 characters ~= 1 token`. Treat them as directional
maintenance metrics, not billing-grade accounting.

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
5. Confirm `workspace/memory/semantic_index.jsonl` exists.
6. Confirm `workspace/memory/semantic_vectors.jsonl` exists.
7. Confirm `output/maintenance/YYYY-MM-DD-conversation-digest.md` exists.
8. Confirm `output/maintenance/` has Markdown and HTML reports if enabled.
9. Confirm the Markdown report includes `## Token Savings`,
   `## Semantic Routing`, and `## Potential Conflicts`.
10. Confirm `output/maintenance/index.html` opens as the Memory Observatory page.
11. For scheduler install, confirm `Get-ScheduledTask -TaskName IronAgentDailyMaintenance`.
12. Confirm Codex automation is active when available.
13. Run `system/scripts/health_check.py`.
