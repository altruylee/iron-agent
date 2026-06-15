# End-to-End Demo

## Directory

- [Purpose](#purpose)
- [Reproduce](#reproduce)
- [What To Inspect](#what-to-inspect)

## Purpose

This demo shows the v0.2.0 value path: initialize a workspace, record task friction, and generate an evolution report.

## Reproduce

From the repository root:

```bash
python -m pip install -e .
iron init ../iron-agent-e2e-demo --overwrite
iron doctor ../iron-agent-e2e-demo --fix
iron report ../iron-agent-e2e-demo
iron task list examples/end-to-end-demo/workspace-state
```

The checked-in `workspace-state/` folder is a sanitized sample of the final state.

## What To Inspect

- `INPUT.md` contains the simulated user conversation.
- `conversation-transcript.md` records the maintenance run.
- `workspace-state/logs/task-log.jsonl` contains five task entries.
- `workspace-state/logs/friction-log.md` contains repeated friction.
- `workspace-state/evolution/2026-06-13-evolution-report.md` contains skill and memory candidates.
- `BEFORE-AFTER.md` explains the token and behavior difference.
