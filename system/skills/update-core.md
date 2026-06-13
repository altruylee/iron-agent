# Update Core Skill

Use this skill to update Iron Agent core files from a newer pack copy while
preserving user data.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Policy](#policy)
- [Process](#process)

## Read Path From Here

| Need | Next file |
|---|---|
| Update script | `system/scripts/update_core.py` |
| Manifest | `manifest.json` |
| User memory | `workspace/meta/memory.md` |
| Domain agents | `packs/domain-agents/` |

## Policy

- Preserve user data by default.
- Never overwrite `workspace/meta/memory.md`, `task-log.jsonl`, `wiki/`,
  `packs/domain-agents/`, `watchlists/`, or `hypotheses/` unless the user
  explicitly asks.
- Run with `--dry-run` first.

## Process

Preview:

```bash
python system/scripts/update_core.py --root . --source {new-pack-path} --dry-run
```

Apply after confirmation:

```bash
python system/scripts/update_core.py --root . --source {new-pack-path} --apply
```

