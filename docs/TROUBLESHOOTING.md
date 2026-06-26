# Troubleshooting

## Directory

- [Use This First](#use-this-first)
- [Common Problems](#common-problems)

## Use This First

Run diagnostics from the workspace root:

```bash
iron doctor . --fix
iron check .
```

## Common Problems

| Error or symptom | Likely cause | Fix | Command |
|---|---|---|---|
| `install_status` stays `0` | Workspace was copied but not initialized | Let CLI write the state | `iron doctor . --fix` |
| Codex does not read `AGENTS.md` | Wrong folder opened | Open the workspace root | `iron doctor .` |
| `evolution_report.py` says no task log | No runtime log exists yet | Create or touch the task log | `iron doctor . --fix` |
| Windows scheduled task is missing | Scheduler is opt-in | Install later from maintenance docs | `Get-Content system/skills/daily-maintenance.md` |
| Chinese text is garbled | Console encoding mismatch | Force UTF-8 in shell | `chcp 65001` |
| `iron` command not found | CLI not installed | Install editable package | `python -m pip install -e .` |
| Memory search has no results | Query does not match local memory | Route by task topic first | `iron memory route . "用户注册"` |
| `task-log.jsonl` has JSON errors | Manual edit broke a line | Show invalid entries | `iron task list .` |
| `shadow_reviewer` fails | Missing task or friction data | Generate report from current logs | `iron evolve .` |
| Evolution candidate not generated | Threshold not reached | Add real task logs first | `iron task list .` |
| Path separator problems | Command copied between shells | Quote paths | `iron check "D:\path\to\workspace"` |
| Python version too low | Python < 3.10 | Install supported Python | `python --version` |
| Permission tier mismatch | Task needs approval | Re-read permission rules | `Get-Content system/skills/codex-agent.md` |
| Domain agent not routed | No matching keywords or pack | Inspect domain index | `Get-Content packs/domain-agents/INDEX.md` |
| Schema validation fails | Required file missing | Restore required files | `iron check . --json` |
| Wiki and memory conflict | Content stored in both places | Follow boundary document | `Get-Content wiki/_schema.md` |
| Dashboard does not open | Local port is occupied or browser launch failed | Start with another port or use CLI | `iron web . --port 8766` |
| Starter pack fails | Starter packs are planned for v0.3.0 | Use current examples | `Get-ChildItem examples` |
| Evolution threshold is unclear | Threshold config is planned for v0.3.0 | Use report recommendations | `iron report .` |
| CI fails on `iron check` | Manifest required files missing | Read missing list | `iron check .` |
| `manifest.json` cannot parse | Invalid JSON | Validate and fix syntax | `python -m json.tool manifest.json` |
| `iron init` refuses target | Target is not empty | Pick empty folder or overwrite | `iron init ./demo --overwrite` |
| `iron doctor` returns `FAIL` | Non-reversible issue remains | Read fix line below failed check | `iron doctor .` |
| Report is empty | No task entries yet | Run demo or append logs | `Get-Content examples/end-to-end-demo/README.md` |
