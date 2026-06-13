# Domain Agent Import Skill

Use this skill when the user provides an existing agent file, domain prompt,
workflow guide, or professional rules file that should become a reusable Iron
Agent domain agent.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Purpose](#purpose)
- [Import Process](#import-process)
- [Runtime Enforcement](#runtime-enforcement)
- [Verification](#verification)

## Read Path From Here

| Need | Next file |
|---|---|
| Domain registry | `packs/domain-agents/INDEX.md` |
| Import script | `system/scripts/import_domain_agent.py` |
| Runtime router | `system/scripts/domain_agent_router.py` |
| Execution protocol | `system/skills/codex-agent.md` |
| Structure check | `system/scripts/structure_integrity.py` |

## Purpose

Turn a user-provided agent file into a registered domain agent that future Codex
sessions can discover and enforce before matching tasks.

## Import Process

1. Ask the user for the local source file path unless already provided.
2. If the domain is obvious, pass it with `--domain`; otherwise let the script infer it.
3. Run:

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

It also updates `packs/domain-agents/INDEX.md`.

## Runtime Enforcement

For any matching task:

1. Check `packs/domain-agents/INDEX.md`.
2. Run or mentally apply `system/scripts/domain_agent_router.py`.
3. Read the matching `{domain}/RUNTIME.md`.
4. Read `{domain}/RULES.md`.
5. Apply mandatory rules before answering or editing.
6. If a rule conflicts with the user's latest request, ask before continuing.
7. Log the domain agent when task logging is performed.

## Verification

After import or update:

1. Run `python system/scripts/structure_integrity.py --root .`.
2. Run `python system/scripts/health_check.py --root .`.
3. Confirm the new domain is listed in `packs/domain-agents/INDEX.md`.
