# Domain Agents

## Directory

- [Purpose](#purpose)
- [Registered Domain Agents](#registered-domain-agents)
- [Recommended Layout](#recommended-layout)
- [Import During Install](#import-during-install)
- [Rules](#rules)

## Purpose

This folder is reserved for user-created domain agents and field packs. Put
personal, field-specific workflows here instead of bloating the core pack.

Examples:

- business agents,
- coding agents,
- writing agents,
- research agents,
- operations agents,
- any user-specific professional workflow.

## Registered Domain Agents

| Domain | Runtime | Rules | Source Agent | Status |
|---|---|---|---|---|

## Recommended Layout

```text
packs/domain-agents/
  development/
    AGENT.md
    RULES.md
    RUNTIME.md
    source-info.json
```

## Rules

- Every Markdown file should include `## Directory`.
- Keep secrets out of this folder.
- Run `system/scripts/audit_skill.py` before promoting any domain skill into `system/skills/`.
- Prefer domain agents here; keep core skills generic.

## Import During Install

During initial install, users may provide an existing `AGENTS.md`, `CLAUDE.md`,
domain prompt, or workflow file. Import it with:

```bash
python system/scripts/import_domain_agent.py --root . --source {path}
```

The importer creates:

```text
packs/domain-agents/{domain}/AGENT.md
packs/domain-agents/{domain}/RULES.md
packs/domain-agents/{domain}/RUNTIME.md
packs/domain-agents/{domain}/source-info.json
```

Imported domain agents are active runtime overlays. For matching tasks, read
`RUNTIME.md` and `RULES.md` before ordinary execution. Promote them into core
skills only after audit and explicit user confirmation.
