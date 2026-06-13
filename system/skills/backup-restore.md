# Backup Restore Skill

Use this skill to back up or restore Iron Agent user state.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Backup](#backup)
- [Restore](#restore)
- [Policy](#policy)

## Read Path From Here

| Need | Next file |
|---|---|
| Backup script | `system/scripts/backup_workspace.py` |
| Restore script | `system/scripts/restore_workspace.py` |
| Backup output | `backups/` |
| User memory | `workspace/meta/memory.md` |
| Wiki | `wiki/` |
| Domain agents | `packs/domain-agents/` |

## Backup

Run:

```bash
python system/scripts/backup_workspace.py --root .
```

The backup includes durable user state: workspace meta, wiki, domain agents,
watchlists, hypotheses, config, and task logs.

## Restore

Preview first:

```bash
python system/scripts/restore_workspace.py --root . --archive {zip} --dry-run
```

Apply only after user confirmation:

```bash
python system/scripts/restore_workspace.py --root . --archive {zip} --apply
```

## Policy

- Backup is P1.
- Restore is P3 when it overwrites existing files.
- Do not include secrets unless the user explicitly asks and confirms.

