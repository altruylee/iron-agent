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
| Layered memory | `workspace/memory/` |
| Domain agents | `packs/domain-agents/` |

## Policy

- Preserve user data by default.
- Never overwrite `workspace/meta/`, `workspace/memory/`, `wiki/`,
  `packs/domain-agents/`, `watchlists/`, `hypotheses/`, `inbox/`, `output/`,
  `backups/`, or `tools/packages/` unless the user explicitly asks.
- Run with `--dry-run` first.

## Process

Preferred one-command update:

```bash
iron update . --source {new-pack-path}
```

Preview first:

```bash
iron update . --source {new-pack-path} --dry-run
```

Low-level script preview:

```bash
python system/scripts/update_core.py --root . --source {new-pack-path} --dry-run
```

Low-level script apply:

```bash
python system/scripts/update_core.py --root . --source {new-pack-path} --apply
```

After updating:

```bash
python system/scripts/health_check.py --root .
python system/scripts/daily_maintenance.py --root . --force
```
