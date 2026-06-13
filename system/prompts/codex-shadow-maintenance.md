# Codex Shadow Maintenance Prompt

## Directory

- [Role](#role)
- [Read Path](#read-path)
- [Allowed Work](#allowed-work)
- [Forbidden Work](#forbidden-work)
- [Verification](#verification)
- [Output](#output)

## Role

Run Iron Agent AI shadow maintenance for the current workspace.

## Read Path

Read only these entry points unless a queued file links to a narrower target:

1. `AGENTS.md`
2. `system/skills/codex-agent.md`
3. `system/skills/codex-automation.md`
4. `workspace/meta/codex-automation-trigger.json`
5. `workspace/memory/shadow-review/INDEX.md`
6. queued files under `workspace/memory/shadow-review/`

## Allowed Work

- Review queued shadow-review files.
- Promote stable SOP bullets to matching files under `workspace/memory/semantic/sops/`.
- Shrink processed queue files to links and status notes.
- Run `python system/scripts/shadow_reviewer.py --root .`.
- Run structure and health checks.

## Forbidden Work

- Do not read full chat history.
- Do not scan all memory.
- Do not process unrelated episode folders.
- Do not merge global memory unless explicitly queued.
- Do not call external services.
- Do not delete user data.
- Do not invent missing business rules.

## Verification

Run:

```bash
python system/scripts/structure_integrity.py --root .
python system/scripts/health_check.py --root .
```

## Output

Return a concise maintenance result:

- queued files processed,
- SOP files updated,
- checks run,
- blockers, if any.
